import hashlib
import logging
import os
import re
from dotenv import load_dotenv

from fastapi import Body, FastAPI, UploadFile, HTTPException, Response, status
from fastapi.responses import FileResponse
import httpx
from bs4 import BeautifulSoup


from bg_replace import background_replace

load_dotenv()
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY")
DISCOURSE_USERNAME = os.getenv("DISCOURSE_USERNAME")
DISCOURSE_USER_ID = int(os.getenv("DISCOURSE_USER_ID"))
DISCOURSE_BASE_URL = os.getenv("DISCOURSE_BASE_URL")
REQUIRED_TITLE_KEYWORD = os.getenv("REQUIRED_TITLE_KEYWORD")

app = FastAPI()
headers = {"Api-Key": DISCOURSE_API_KEY, "Api-Username": DISCOURSE_USERNAME}
logger = logging.Logger("fastapi")


def save_file(data: bytes, filename: str):
    ext_img = filename.split(".")[-1]
    name_img = hashlib.new("sha1", data).hexdigest() + "." + ext_img
    path_img = os.path.join("uploads", name_img)
    with open(path_img, mode="wb") as f:
        f.write(data)
    return name_img, path_img


@app.post("/replace/")
async def create_upload_file(img: UploadFile, bg: UploadFile):
    data_img = await img.read()
    name_img, path_img = save_file(data_img, img.filename)

    data_bg = await bg.read()

    path_out = os.path.join("output", name_img)
    background_replace(path_img,
                       data_bg, path_out)
    # return {"msg": "OK"}
    # return StreamingResponse(buf, media_type="image/jpeg")
    return FileResponse(path_out)


def extract_url_from_lightbox(node) -> str:
    url = node['data-download-href']
    if url.startswith("//"):
        return "http:" + url
    return url


def extract_url_from_img(node) -> str:
    url = node['src']
    filename = url.split("/")[-1].split(".")[0]
    return f"{DISCOURSE_BASE_URL}/uploads/default/{filename}"


async def get_post_detail(client: httpx.AsyncClient, post_id: int):
    resp = await client.get(f"{DISCOURSE_BASE_URL}/posts/{post_id}.json")
    if resp.status_code != httpx.codes.OK:
        logger.error("Cannot load post detail")
        raise HTTPException(status_code=500, detail="Cannot load post detail")
    return resp.json()


def parse_image_urls(post: dict) -> list[str]:
    cooked: str = post['cooked']
    soup = BeautifulSoup(cooked, "html.parser")

    image_urls = []
    # try eventually cooked (include a, lightbox)
    html_nodes: list = soup.find_all("a", "lightbox")

    if len(html_nodes) >= 2:
        image_urls: list[str] = list(map(
            extract_url_from_lightbox,  html_nodes))
    elif len(html_nodes) < 2:
        # try partially cooked
        html_nodes: list = soup.find_all("img")
        image_urls: list[str] = list(map(
            extract_url_from_img,  html_nodes))
    return image_urls


async def download_from_discourse(client: httpx.AsyncClient, image_urls):
    resp_front = await client.get(image_urls[0])
    if resp_front.status_code != httpx.codes.OK:
        logger.error("Cannot download first image")
        raise HTTPException(
            status_code=500, detail="Cannot download first image")
    resp_bg = await client.get(image_urls[1])
    if resp_bg.status_code != httpx.codes.OK:
        logger.error("Cannot download second image")
        raise HTTPException(
            status_code=500, detail="Cannot download second image")
    return resp_front, resp_bg


async def reply_to_discourse(client: httpx.AsyncClient, topic_id: str, path_out: str):
    resp_upload = await client.post(f"{DISCOURSE_BASE_URL}/uploads.json",
                                    data={"type": "composer"}, files={'file': open(path_out, 'rb')})
    if resp_upload.status_code != httpx.codes.OK:
        logger.error("Cannot upload replaced image")
        raise HTTPException(
            status_code=500, detail="Cannot upload replaced image")
    uploaded = resp_upload.json()
    short_url = uploaded['short_url']
    original_filename = uploaded['original_filename']
    width = uploaded['width']
    height = uploaded['height']

    resp_new_pm = await client.post(f"{DISCOURSE_BASE_URL}/posts.json", json={
        "raw": f"![{original_filename}|{width}x{height}]({short_url})",
        "topic_id": topic_id,
    })
    if resp_new_pm.status_code != httpx.codes.OK:
        logger.error("Cannot reply PM")
        raise HTTPException(status_code=500, detail="Cannot reply PM")


@app.post("/webhook/", status_code=200)
async def webhook(response: Response, body=Body()):
    notification = body['notification']

    user_id = notification['user_id']
    if user_id != DISCOURSE_USER_ID:
        return {"detail": "Not for Bot"}
    read = notification['read']
    if read:
        return {"detail": "Already responsed"}
    notification_type = notification['notification_type']
    if notification_type != 6:
        return {"detail": "Not a PM"}
    post_id = notification['data']['original_post_id']
    title = notification['data']['topic_title']
    if REQUIRED_TITLE_KEYWORD not in title:
        return {"detail": "No required title"}

    topic_id = notification['topic_id']
    # get post detail, get image urls
    client = httpx.AsyncClient(headers=headers)

    post = await get_post_detail(client, post_id)
    image_urls = parse_image_urls(post)

    if len(image_urls) < 2:
        logger.error("No enough images")
        raise HTTPException(status_code=400, detail="No enough images")

    # download images from Discourse
    resp_front, resp_bg = await download_from_discourse(client, image_urls)
    bg = resp_bg.content

    # do replace
    reg = re.compile("filename=\"(.+)\"")
    fname = reg.findall(resp_front.headers["Content-Disposition"])[0]
    name_img, path_img = save_file(resp_front.content, fname)

    path_out = os.path.join("output", name_img)
    background_replace(path_img,
                       bg, path_out)

    # upload result to Discourse
    await reply_to_discourse(client, topic_id, path_out)

    # mark nofitification as read
    await client.put(f"{DISCOURSE_BASE_URL}/notifications/mark-read.json", json={
        "id": notification['id'],
    })
    # response to webhook
    response.status_code = status.HTTP_201_CREATED
    return {"detail": "All OK"}
