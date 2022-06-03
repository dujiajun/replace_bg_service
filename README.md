# 替换背景（某活动限定）
---

基于 PaddlePaddle 的 [PaddleSeg](https://github.com/PaddlePaddle/PaddleSeg/) 套件

## 如何使用

Python 版本要求

* Python >= 3.7+

### 安装依赖
PaddlePaddle：参考 https://www.paddlepaddle.org.cn/install/quick

其他（PaddleSeg, FastApi, Uvicorn）：
```
pip install -r requirements.txt
```

### 下载模型
打开`models/download_export_model.py`文件，修改`model_urls`变量。

模型可参见 [可用模型列表](https://github.com/PaddlePaddle/PaddleSeg/blob/release/2.5/Matting/README_CN.md#模型) ，使用最后一列 Inference Model 提供的地址。

### 运行 Web 服务
```
uvicorn main:app --reload
```