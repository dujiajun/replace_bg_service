# coding: utf8
# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserve.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from paddleseg.utils.download import download_file_and_uncompress
import sys
import os

LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))


model_urls = {
    "modnet-mobilenetv2": "https://paddleseg.bj.bcebos.com/matting/models/deploy/modnet-mobilenetv2.zip",
    "pp-matting-hrnet_w18-human_1024": "https://paddleseg.bj.bcebos.com/matting/models/deploy/pp-matting-hrnet_w18-human_1024.zip",
    "pp-humanmatting-resnet34_vd": "https://paddleseg.bj.bcebos.com/matting/models/deploy/pp-humanmatting-resnet34_vd.zip"
}

if __name__ == "__main__":
    for model_name, url in model_urls.items():
        download_file_and_uncompress(
            url=url,
            savepath=LOCAL_PATH,
            extrapath=LOCAL_PATH,
            extraname=model_name)

    print("Export model download success!")
