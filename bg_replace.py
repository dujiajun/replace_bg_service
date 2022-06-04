import cv2
import numpy as np

from deploy.mat_infer import Predictor, parse_args


predictor = None


def background_replace(img_path, bg_img, out_img_path):
    global predictor
    args = parse_args(['--config', 'models/pp-humanmatting-resnet34_vd/deploy.yaml',
                       '--image_path', img_path, '--save_dir', './output'])

    if predictor is None:
        predictor = Predictor(args)
    alphas = predictor.run(imgs=[args.image_path])
    alpha = alphas[0]

    img = cv2.imread(args.image_path)
    bg = cv2.imdecode(np.frombuffer(bg_img, dtype=np.uint8), cv2.IMREAD_COLOR)
    h, w, _ = img.shape
    bg = cv2.resize(bg, (w, h))
    if bg.ndim == 2:
        bg = bg[..., np.newaxis]
    if alpha.ndim == 2:
        alpha = alpha[..., np.newaxis]
    comb = (alpha * img +
            (1 - alpha) * bg).astype(np.uint8)

    cv2.imwrite(out_img_path, comb)
