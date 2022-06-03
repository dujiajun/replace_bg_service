import hashlib
import os

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse

from bg_replace import background_replace

app = FastAPI()


@app.post("/replace/")
async def create_upload_file(img: UploadFile, bg: UploadFile):
    data_img = await img.read()
    ext_img = img.filename.split(".")[-1]
    name_img = hashlib.new("sha1", data_img).hexdigest() + "." + ext_img
    path_img = os.path.join("uploads", name_img)
    with open(path_img, mode="wb") as f:
        f.write(data_img)

    data_bg = await bg.read()
    ext_bg = bg.filename.split(".")[-1]
    name_bg = hashlib.new("sha1", data_bg).hexdigest() + "." + ext_bg
    path_bg = os.path.join("uploads", name_bg)
    with open(path_bg, mode="wb") as f:
        f.write(data_bg)

    name_out = hashlib.new(
        "sha1", (name_img + name_bg).encode("utf-8")).hexdigest() + ".jpg"
    path_out = os.path.join("output", name_out)
    background_replace(path_img,
                       path_bg, path_out)
    # return {"msg": "OK"}
    return FileResponse(path_out)
