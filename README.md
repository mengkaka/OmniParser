# OmniParser: Screen Parsing tool for Pure Vision Based GUI Agent

<p align="center">
  <img src="imgs/logo.png" alt="Logo">
</p>
<!-- <a href="https://trendshift.io/repositories/12975" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12975" alt="microsoft%2FOmniParser | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a> -->

[![arXiv](https://img.shields.io/badge/Paper-green)](https://arxiv.org/abs/2408.00203)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

📢 [[Project Page](https://microsoft.github.io/OmniParser/)] [[V2 Blog Post](https://www.microsoft.com/en-us/research/articles/omniparser-v2-turning-any-llm-into-a-computer-use-agent/)] [[Models V2](https://huggingface.co/microsoft/OmniParser-v2.0)] [[Models V1.5](https://huggingface.co/microsoft/OmniParser)] [[HuggingFace Space Demo](https://huggingface.co/spaces/microsoft/OmniParser-v2)]

**OmniParser** is a comprehensive method for parsing user interface screenshots into structured and easy-to-understand elements, which significantly enhances the ability of GPT-4V to generate actions that can be accurately grounded in the corresponding regions of the interface. 

## News
- [2025/3] We support local logging of trajecotry so that you can use OmniParser+OmniTool to build training data pipeline for your favorate agent in your domain. [Documentation WIP]
- [2025/3] We are gradually adding multi agents orchstration and improving user interface in OmniTool for better experience.
- [2025/2] We release OmniParser V2 [checkpoints](https://huggingface.co/microsoft/OmniParser-v2.0). [Watch Video](https://1drv.ms/v/c/650b027c18d5a573/EWXbVESKWo9Buu6OYCwg06wBeoM97C6EOTG6RjvWLEN1Qg?e=alnHGC)
- [2025/2] We introduce OmniTool: Control a Windows 11 VM with OmniParser + your vision model of choice. OmniTool supports out of the box the following large language models - OpenAI (4o/o1/o3-mini), DeepSeek (R1), Qwen (2.5VL) or Anthropic Computer Use. [Watch Video](https://1drv.ms/v/c/650b027c18d5a573/EehZ7RzY69ZHn-MeQHrnnR4BCj3by-cLLpUVlxMjF4O65Q?e=8LxMgX)
- [2025/1] V2 is coming. We achieve new state of the art results 39.5% on the new grounding benchmark [Screen Spot Pro](https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding/tree/main) with OmniParser v2 (will be released soon)! Read more details [here](https://github.com/microsoft/OmniParser/tree/master/docs/Evaluation.md).
- [2024/11] We release an updated version, OmniParser V1.5 which features 1) more fine grained/small icon detection, 2) prediction of whether each screen element is interactable or not. Examples in the demo.ipynb. 
- [2024/10] OmniParser was the #1 trending model on huggingface model hub (starting 10/29/2024). 
- [2024/10] Feel free to checkout our demo on [huggingface space](https://huggingface.co/spaces/microsoft/OmniParser)! (stay tuned for OmniParser + Claude Computer Use)
- [2024/10] Both Interactive Region Detection Model and Icon functional description model are released! [Hugginface models](https://huggingface.co/microsoft/OmniParser)
- [2024/09] OmniParser achieves the best performance on [Windows Agent Arena](https://microsoft.github.io/WindowsAgentArena/)! 

## Install 
First clone the repo, and then install environment:
```python
cd OmniParser
conda create -n "omni" python==3.12
conda activate omni
pip install -r requirements.txt
```

Ensure you have the V2 weights downloaded in weights folder (ensure caption weights folder is called icon_caption_florence). If not download them with:
```
   # download the model checkpoints to local directory OmniParser/weights/
   for f in icon_detect/{train_args.yaml,model.pt,model.yaml} icon_caption/{config.json,generation_config.json,model.safetensors}; do huggingface-cli download microsoft/OmniParser-v2.0 "$f" --local-dir weights; done
   mv weights/icon_caption weights/icon_caption_florence
```

<!-- ## [deprecated]
Then download the model ckpts files in: https://huggingface.co/microsoft/OmniParser, and put them under weights/, default folder structure is: weights/icon_detect, weights/icon_caption_florence, weights/icon_caption_blip2. 

For v1: 
convert the safetensor to .pt file. 
```python
python weights/convert_safetensor_to_pt.py

For v1.5: 
download 'model_v1_5.pt' from https://huggingface.co/microsoft/OmniParser/tree/main/icon_detect_v1_5, make a new dir: weights/icon_detect_v1_5, and put it inside the folder. No weight conversion is needed. 
``` -->

## Examples:
We put together a few simple examples in the demo.ipynb. 

## Gradio Demo
To run gradio demo, simply run:
```python
python gradio_demo.py
```

本 fork 中 Gradio 会按 `cuda → mps → cpu` 自动选择推理设备，并监听 `0.0.0.0:7861`（局域网可访问，`share=False`）。

---

## 本地修改说明

本仓库在 [microsoft/OmniParser](https://github.com/microsoft/OmniParser) 基础上做了以下扩展，便于在 **Mac（Apple Silicon）** 上长期运行 HTTP 服务，并从局域网或其它机器调用。

### 1. Apple Silicon / 多设备推理（`util/utils.py`、`util/omniparser.py`）

- 新增 `get_torch_device()`、`resolve_torch_device()`：设备优先级为 **CUDA → MPS → CPU**；CLI/API 支持 `--device auto|cpu|cuda|mps`。
- Florence2 图标描述在 **CUDA 与 MPS** 上均使用 `float16`，在 CPU 上使用 `float32`。
- `Omniparser` 初始化时按配置解析设备，并在日志中打印当前设备。

### 2. FastAPI 服务增强（`omnitool/omniparserserver/omniparserserver.py`）

| 变更 | 说明 |
|------|------|
| 默认监听 | `--host 0.0.0.0`（本机 + 局域网） |
| 默认设备 | `--device auto` |
| 新参数 | `--iou_threshold`（默认 `0.7`，与检测框合并相关） |
| `GET /probe/` | 返回 `device`、`box_threshold`、`iou_threshold` |
| `POST /parse/` | 支持按请求控制输出内容与阈值（见下表） |
| 错误处理 | 非法参数返回 HTTP 400 |
| 启动方式 | `uvicorn.run(app, reload=False)`，避免 reload 导致模型重复加载 |

**`POST /parse/` 请求体（在原有 `base64_image` 之外）：**

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `response_mode` | `"all"` \| `"image"` \| `"json"` | `"all"` | `all`：标注图 + JSON；`image`：仅标注图；`json`：仅 JSON |
| `return_parsed_content` | `bool` | `true` | 为 `false` 时只做 OCR + 框，不跑 Florence2 图标语义（`json`/`all` 模式下有效） |
| `box_threshold` | `float?` | 服务端默认 `0.05` | 图标检测置信度，越高框越少 |
| `iou_threshold` | `float?` | 服务端默认 `0.7` | 重叠框合并阈值 |

手动启动示例：

```bash
python -m omnitool.omniparserserver.omniparserserver \
  --som_model_path weights/icon_detect/model.pt \
  --caption_model_name florence2 \
  --caption_model_path weights/icon_caption_florence \
  --device auto --host 0.0.0.0 --port 8000
```

完整接口说明见 [`launchd/API.md`](launchd/API.md)（含 curl 示例与 `response_mode` 组合说明）。

### 3. 推理管线修复与优化（`util/utils.py`、`util/omniparser.py`）

- **`get_som_labeled_img`**：新增 `return_som_image`，可在只要 JSON、不要标注图时跳过绘图与 PNG 编码。
- **空检测 / 边界情况**：无有效框时仍可按需返回原图 base64 或空列表，避免异常。
- **`starting_idx == 0`**：修正「首个待 caption 图标下标为 0」时被误判为 falsy 的 bug。
- **PaddleOCR**：兼容 2.x 与 3.x（`paddlex` OCRResult）输出格式。
- **OCR bbox**：归一化与空列表处理更稳健。

### 4. 依赖（`requirements.txt`）

- 将 `transformers` 固定为 **`4.41.2`**，与 Florence2 远程代码加载行为保持一致。

### 5. macOS 开机自启（`launchd/`）

通过 **launchd User Agent** 在后台常驻 FastAPI 服务：

| 文件 | 作用 |
|------|------|
| `launchd/com.omniparser.server.plist` | 服务模板（`0.0.0.0:8000`、`device=auto`、权重路径等） |
| `launchd/load.sh` | 解析 conda `omni` 环境、安装 plist、启动服务 |
| `launchd/unload.sh` | 停止并卸载服务 |
| `launchd/API.md` | HTTP API 文档 |
| `logs/omniparser.{stdout,stderr}.log` | 运行日志（由 plist 写入，目录需存在） |

```bash
# 安装并启动（需已 conda activate omni 且 weights 已下载）
./launchd/load.sh

# 健康检查（Mac M 系列上 device 通常为 mps）
curl http://127.0.0.1:8000/probe/

# 停止服务
./launchd/unload.sh
```

可通过环境变量 `OMNIPARSER_PYTHON` 指定 Python 解释器路径。`load.sh` 会优先使用 `~/miniconda3/envs/omni/bin/python` 或 `~/anaconda3/envs/omni/bin/python`。

### 修改文件一览

| 路径 | 概要 |
|------|------|
| `util/utils.py` | MPS/自动设备、PaddleOCR 兼容、SOM 管线修复 |
| `util/omniparser.py` | `response_mode`、按请求阈值、可选返回字段 |
| `omnitool/omniparserserver/omniparserserver.py` | API 扩展、probe、LAN 监听 |
| `gradio_demo.py` | 自动设备、`0.0.0.0` 绑定 |
| `requirements.txt` | `transformers==4.41.2` |
| `launchd/*` | macOS 守护进程与 API 文档（新增） |

---

## Model Weights License
For the model checkpoints on huggingface model hub, please note that icon_detect model is under AGPL license since it is a license inherited from the original yolo model. And icon_caption_blip2 & icon_caption_florence is under MIT license. Please refer to the LICENSE file in the folder of each model: https://huggingface.co/microsoft/OmniParser.

## 📚 Citation
Our technical report can be found [here](https://arxiv.org/abs/2408.00203).
If you find our work useful, please consider citing our work:
```
@misc{lu2024omniparserpurevisionbased,
      title={OmniParser for Pure Vision Based GUI Agent}, 
      author={Yadong Lu and Jianwei Yang and Yelong Shen and Ahmed Awadallah},
      year={2024},
      eprint={2408.00203},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2408.00203}, 
}
```
