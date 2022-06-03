import os
import cv2
from cv2 import imread
import numpy as np

from deploy.mat_infer import Predictor, parse_args


predictor = None


def background_replace(img_path, bg_img_path, out_img_path):
    global predictor
    args = parse_args(['--config', 'models/pp-matting-hrnet_w18-human_1024/deploy.yaml',
                       '--image_path', img_path, '--save_dir', './output'])

    if predictor is None:
        predictor = Predictor(args)

    img = cv2.imread(args.image_path)
    bg = cv2.imread(bg_img_path)

    predictor.run(imgs=[args.image_path])
    print(os.path.join("./output", img_path.split(".")[0]+ ".png"))
    alpha = cv2.imread(os.path.join("./output/alpha", img_path.split(".")[0]+ ".png"))
    alpha = alpha / 255.0
    h, w, _ = img.shape
    bg = cv2.resize(bg, (w, h))
    if bg.ndim == 2:
        bg = bg[..., np.newaxis]

    comb = (alpha * img + (1 - alpha) * bg).astype(np.uint8)
    cv2.imwrite(out_img_path, comb)
