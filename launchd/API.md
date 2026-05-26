# OmniParser FastAPI 接口说明

本文档描述由 **launchd** 托管的服务：

```bash
python -m omnitool.omniparserserver.omniparserserver
```

默认监听 **`0.0.0.0:8000`**（本机与局域网均可访问）。

---

## 服务地址

| 环境 | 地址示例 |
|------|----------|
| 本机 | `http://127.0.0.1:8000` |
| 局域网 | `http://<Mac的IP>:8000`（如 `http://192.168.1.23:8000`） |

查看本机 IP：

```bash
ipconfig getifaddr en0
```

---

## Mac M 系列设备（推荐配置）

launchd 默认 `--device auto`，启动顺序：

1. **CUDA**（无 NVIDIA 则跳过）
2. **MPS**（Apple Silicon GPU，统一内存架构）
3. **CPU**（兜底）

在 Mac Studio / M 系列上，应看到 `/probe/` 返回 `"device": "mps"`。Florence2 图标描述会走 GPU，通常比纯 CPU **快数倍**。

重载服务使配置生效：

```bash
./launchd/unload.sh && ./launchd/load.sh
curl http://127.0.0.1:8000/probe/
```

---

## 接口总览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/probe/` | 健康检查 + 当前设备与默认阈值 |
| `POST` | `/parse/` | 解析屏幕截图（核心接口） |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc 文档 |
| `GET` | `/openapi.json` | OpenAPI Schema |

---

## 1. 健康检查

### `GET /probe/`

**响应示例（200）：**

```json
{
  "message": "Omniparser API ready",
  "device": "mps",
  "box_threshold": 0.05,
  "iou_threshold": 0.7
}
```

```bash
curl http://127.0.0.1:8000/probe/
```

---

## 2. 解析截图

### `POST /parse/`

**Content-Type：** `application/json`

### 请求体

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `base64_image` | `string` | 是 | — | 图片标准 Base64（**不要** `data:image/...;base64,` 前缀） |
| `response_mode` | `string` | 否 | `"all"` | 返回模式：`"all"` \| `"image"` \| `"json"` |
| `return_parsed_content` | `boolean` | 否 | `true` | 是否做 **Florence2 图标语义**；见下表 |
| `box_threshold` | `number` | 否 | 服务端 `0.05` | 不传 = 源代码 API 默认；传了才改变检测灵敏度 |
| `iou_threshold` | `number` | 否 | 服务端 `0.7` | 不传 = 源代码 API 默认；传了才改变重叠合并 |

1）box_threshold（检测置信度）
作用阶段：YOLO 检 icon 时。
含义：模型对每个框有一个置信度；低于该值的框直接丢掉。
调高（如 0.05 → 0.15）：框 更少，小、糊、不确定的 icon 更容易被丢掉 → 更快，可能 漏检。
调低：框 更多，更慢，更全。
不是「服务最多只分析 N 个 icon」的硬上限，而是 过滤检出的框。

2）iou_threshold（重叠合并）
作用阶段：YOLO 框与 OCR 框合并、去掉重复/重叠时。
含义：两个框重叠程度（IOU）超过该阈值时，认为重复，合并/去掉其中一个。
调高（如 0.7 → 0.9）：合并 更狠 → 最终框 更少 → Florence2 次数少 → 更快，贴得很近的两个按钮可能被合成一个。
调低：保留更多独立框。

### `response_mode` 与 `return_parsed_content` 组合（重要）

| `response_mode` | `return_parsed_content` | 响应内容 | Florence2 图标描述 | 说明 |
|--------------|-------------------------|----------|-------------------|------|
| **`all`**（默认） | `true`（默认） | 图 + JSON（含 icon 描述） | 执行 | **与改 API 前完全一致**；只传 `base64_image` 即可 |
| `all` | `false` | 图 + JSON（仅 OCR/框，icon 无描述） | **跳过** | 要图 + 结构，但不要 icon 语义 |
| **`image`** | （任意，**忽略**） | 仅 `som_image_base64` | **跳过** | 只要标注图；`return_parsed_content` 无效 |
| **`json`** | `true` | 仅 `parsed_content_list`（含 icon 描述） | 执行 | 只要 JSON；`box_threshold` / `iou_threshold` **仍生效** |
| `json` | `false` | 仅 `parsed_content_list`（无 icon 描述） | **跳过** | 最快 JSON 之一（无 Florence2） |

要点：

- **`return_parsed_content` 不会忽略 `box_threshold` / `iou_threshold`**。后者始终影响「检出多少框」；前者只控制「要不要对每个 icon 跑 Florence2」。
- `response_mode: "image"` 时不必传 `return_parsed_content`。

### 响应体（200）

| 字段 | 类型 | 何时出现 |
|------|------|----------|
| `latency` | `number` | 始终 |
| `som_image_base64` | `string` | `response_mode` 为 `all` 或 `image` |
| `parsed_content_list` | `array` | `response_mode` 为 `all` 或 `json` |

**`parsed_content_list` 单项：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `string` | `"text"` 或 `"icon"` |
| `bbox` | `array[number]` | `[x1,y1,x2,y2]` 相对坐标 0～1 |
| `interactivity` | `boolean` | 是否可交互 |
| `content` | `string` | OCR 文本或图标描述 |
| `source` | `string` | 可选；OCR 常为 `box_ocr_content_ocr` |

### 请求示例

**完整返回（默认，与原先一致）：**

```json
{
  "base64_image": "iVBORw0KGgo..."
}
```

等价于 `"response_mode": "all", "return_parsed_content": true`。

**只要 JSON（含 icon 描述）：**

```json
{
  "base64_image": "iVBORw0KGgo...",
  "response_mode": "json",
  "return_parsed_content": true
}
```

**只要标注图（忽略 `return_parsed_content`）：**

```json
{
  "base64_image": "iVBORw0KGgo...",
  "response_mode": "image"
}
```

**减少图标数量（提速，见下节）：**

```json
{
  "base64_image": "iVBORw0KGgo...",
  "box_threshold": 0.12,
  "iou_threshold": 0.85
}
```

### curl 示例

```bash
BASE64=$(base64 -i screenshot.png | tr -d '\n')

# 仅 JSON
curl -X POST "http://127.0.0.1:8000/parse/" \
  -H "Content-Type: application/json" \
  -d "{\"base64_image\":\"${BASE64}\",\"response_mode\":\"json\"}"

# 仅标注图
curl -X POST "http://127.0.0.1:8000/parse/" \
  -H "Content-Type: application/json" \
  -d "{\"base64_image\":\"${BASE64}\",\"response_mode\":\"image\"}"
```

### 错误响应

| 状态码 | 说明 |
|--------|------|
| `422` | `response_mode` 不是 `image`/`json`/`all`，或其它字段类型/范围错误 |
| `500` | 推理失败，见 `logs/omniparser.stderr.log` |

---

## 3. 减少 icon 数量（不是“强制上限”）

**不是**服务硬性限制“最多分析 N 个 icon”，而是通过阈值让 **低置信度 / 高度重叠** 的框在检测阶段被过滤掉，从而减少进入 Florence2 的 icon 数量（每个 icon 一次生成，最耗时）。

| 参数 | 调高效果 | 典型范围 |
|------|----------|----------|
| `box_threshold` | YOLO 置信度低的框丢弃 | 默认 `0.05`，可试 `0.10`～`0.20` |
| `iou_threshold` | 重叠框合并更激进，留下更少框 | 默认 `0.7`，可试 `0.8`～`0.9` |

**权衡：** 阈值过高会 **漏检** 小图标或贴得近的按钮；建议在业务可接受范围内逐步调高，观察 `parsed_content_list` 长度与 `latency`。

可在 **单次请求** 里覆盖（无需改 plist）：

```json
{ "base64_image": "...", "box_threshold": 0.15, "iou_threshold": 0.85 }
```

---

## 4. OCR（中英文）

`util/utils.py` 中两套引擎均已按 **简体中文 + 英文** 配置（Gradio / API 共用）：

| 引擎 | 配置 | 何时使用 |
|------|------|----------|
| **EasyOCR** | `Reader(['ch_sim', 'en'])` | API 默认；Gradio **未勾选** PaddleOCR 时 |
| **PaddleOCR** | `lang='ch'` | Gradio **勾选** Use PaddleOCR 时；中英混排 UI 常用 |

说明：

- **繁体中文** 界面可将 EasyOCR 改为 `ch_tra`（需改 `util/utils.py`）。
- 首次启动会下载中文模型，**启动更慢、内存更大**。
- API 当前固定 `use_paddleocr=False`（EasyOCR）；要与网页一致可勾选 Paddle 或后续为 API 增加该参数。

---

## 5. 性能瓶颈（为何慢）

单次 `latency` 大致组成：

1. **OCR（EasyOCR 或 PaddleOCR）** — 数秒～十余秒（中文模型更重）  
2. **YOLO 检测** — 通常 &lt; 1s  
3. **Florence2 对每个 icon 做 `generate`** — **主要卡点**（与 icon 数量近似线性）  
4. **画标注图 + PNG + Base64** — 通常 1～2s（`response_mode: "json"` 时可跳过）

在 **MPS** 上，第 3 步通常比 CPU 快很多；要与官方 CUDA demo 亚秒级相比，仍需 NVIDIA GPU + 较少 icon。

---

## launchd 默认启动参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `--host` | `0.0.0.0` | 局域网可访问 |
| `--port` | `8000` | |
| `--device` | `auto` | Mac 上优选 **mps** |
| `--BOX_TRESHOLD` | `0.05` | 可被请求体 `box_threshold` 覆盖 |
| `--iou_threshold` | `0.7` | 可被请求体 `iou_threshold` 覆盖 |

修改 plist 后：`./launchd/unload.sh && ./launchd/load.sh`

---

## 运维命令

```bash
./launchd/load.sh
./launchd/unload.sh
launchctl print gui/$(id -u)/com.omniparser.server
tail -f logs/omniparser.stdout.log
tail -f logs/omniparser.stderr.log
```

---

## 相关文件

| 文件 | 作用 |
|------|------|
| `launchd/com.omniparser.server.plist` | launchd 模板 |
| `launchd/load.sh` / `unload.sh` | 启停脚本 |
| `omnitool/omniparserserver/omniparserserver.py` | FastAPI 路由 |
| `util/omniparser.py` | 解析与返回模式逻辑 |
| `util/utils.py` | 检测 / OCR / 描述 / 绘图 |
