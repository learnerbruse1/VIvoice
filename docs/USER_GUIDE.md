# VIvoice 使用指南 / User Guide

本页同时提供中文（先）与 English（后）。The Chinese walkthrough comes first,
followed by the English version. 应用内“使用指南”页会渲染本文件；文中的链接在
应用内可直接点击。The in-app guide renders this file, and links are clickable.

---

## 中文版

### 第 1 步：安装 Python 与 uv

1. 安装 Python 3.11–3.13（推荐 3.12）：<https://www.python.org/downloads/>
2. 安装 uv 包管理器：<https://docs.astral.sh/uv/getting-started/installation/>
3. 打开终端，运行 `uv --version` 确认安装成功。

### 第 2 步：获取并安装 VIvoice

```bash
git clone https://github.com/VIvoice/VIvoice.git
cd VIvoice
uv sync --extra dev --extra realtime
```

说明：

- `uv sync` 会创建项目专用虚拟环境并安装依赖，不会污染系统 Python。
- `--extra realtime` 为后续实时功能预装 sounddevice；现在只做离线转换也可省略。

### 第 3 步：启动桌面应用

```bash
uv run vivoice-gui
```

首次启动时，应用会自动检测计算设备（CUDA → MPS → CPU）并在状态栏显示结果。

### 第 4 步：让 AI 音色转换可用（可选但推荐）

1. 安装 AI 依赖（包含 PyTorch 与 rvc-hub 引擎）：

   ```bash
   uv sync --extra ai
   ```

2. 导入一个角色音色模型（见第 5 步），并在预设中使用 `engine: rvc-hub`
   （参考 `examples/presets/ai-voice-rvc-hub.yaml`）。首次转换会从 HuggingFace
   下载基础推理资产（hubert/rmvpe）；网络受限时设置
   `HF_ENDPOINT=https://hf-mirror.com`。

3. 再次启动 GUI，状态栏应显示 CUDA/CPU；若显示 CPU，说明当前环境未检测到可用
   CUDA，程序已自动回退。

进程内上游引擎 `engine: rvc` 仍是可选路径（需要 `python scripts/fetch_rvc.py`
与兼容的 Python 工具链）。若上游 RVC 需要独立环境，可改用客户端/服务端方式：
在有 RVC 环境的那台机器上运行 `vivoice serve`，本机使用
`examples/presets/ai-voice-http.yaml` 预设并填好模型名与服务地址。协议见
<https://github.com/VIvoice/VIvoice/blob/main/docs/RVC_SERVER_PROTOCOL.md>。

### 第 5 步：导入音色模型（两种方式）

方式 A——本地导入（.pth + 可选 .index）：

```bash
vivoice model add path/to/model.pth --name 我的角色 --index path/to/model.index
```

方式 B——从 HuggingFace 下载：

```bash
vivoice model pull <仓库ID，例如 wok000/vcclient000>
```

大型社区仓库包含很多模型时，用 `--path/--index` 只下载需要的文件：

```bash
vivoice model pull chaye741/RVC-Voice-Models \
  --path "weights/卡通-懒羊羊.pth" --index "indices/卡通-懒羊羊.index"
```

模型存放于 `~/.vivoice/models/`。可在 GUI 的“模型”页查看、导入、删除。

模型站点与搜索入口：

- Hugging Face：<https://huggingface.co/>
- voice-models.com：<https://voice-models.com/>
- Weights：<https://www.weights.gg/>

注意：每个音色模型有自己的许可证与训练数据来源；仅克隆你已获得知情同意的声音，
并遵守模型作者的条款。详见 [ETHICS.md](../ETHICS.md)。

### 第 6 步：选择预设并转换

1. GUI “转换”页选择输入音频（WAV/FLAC/OGG）、输出路径。
2. 选择预设（例如 `robot`、`pitch-up`、`deep-voice`），或新建预设。
3. 若要换声线，选择“音色转换”效果并指定一个已导入的音色模型。
4. 点击“开始”。转换在后台线程执行，界面不会卡住。

命令行等价操作：

```bash
vivoice process input.wav output.wav --preset examples/presets/robot.yaml
vivoice effects    # 查看可用效果
vivoice devices    # 查看检测到的计算设备
```

### 第 7 步：实时变声（后续版本）

自 v0.2 起，标有 `[streaming]` 的效果（gain/robot/echo/eq/noise-gate/reverb）
可以先实时预览：

```bash
uv sync --extra realtime
vivoice stream --preset examples/presets/broadcast.yaml
vivoice stream --list-devices
```

GUI 中的 “Live” 页提供同样的实时预览，可选择输入/输出设备、采样率与块大小。
按 `Ctrl+C` 停止。音高偏移与 AI 音色转换目前只支持离线处理；完整实时流
（含这两类效果）属于 v1 里程碑（见 [ROADMAP.md](ROADMAP.md)）。Windows 上实现
“麦克风 → 处理 → 其他应用”需要虚拟声卡：

- VB-Cable（免费，闭源）：<https://vb-audio.com/Cable/>

目标延迟：DSP 链 < 50ms；AI 音色转换按实测标注（参考实现约 150–200ms 端到端）。

### 常见问题

- **状态栏显示 CPU**：未检测到 CUDA。检查 NVIDIA 驱动
  （<https://www.nvidia.com/drivers/>）或使用 `vivoice devices` 查看详情。
- **找不到 RVC 引擎**：先执行第 4 步的 `uv sync --extra ai` 和
  `python scripts/fetch_rvc.py`。
- **模型下载失败**：检查网络能否访问 HuggingFace，必要时设置镜像环境变量
  `HF_ENDPOINT`。

### 参考链接

- RVC 官方仓库：<https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI>
- VIvoice 架构：<https://github.com/VIvoice/VIvoice/blob/main/docs/ARCHITECTURE.md>
- VIvoice 路线图：<https://github.com/VIvoice/VIvoice/blob/main/docs/ROADMAP.md>
- 许可证与第三方：<https://github.com/VIvoice/VIvoice/blob/main/THIRD_PARTY_NOTICES.md>

---

## English

### Step 1: install Python and uv

1. Install Python 3.11–3.13 (3.12 recommended): <https://www.python.org/downloads/>
2. Install uv: <https://docs.astral.sh/uv/getting-started/installation/>
3. Verify with `uv --version`.

### Step 2: get and install VIvoice

```bash
git clone https://github.com/VIvoice/VIvoice.git
cd VIvoice
uv sync --extra dev --extra realtime
```

`uv sync` creates a project-local virtual environment; it does not touch your
system Python. `--extra realtime` pre-installs sounddevice for the upcoming
real-time milestone and is optional today.

### Step 3: launch the desktop app

```bash
uv run vivoice-gui
```

On startup VIvoice detects the compute device (CUDA → MPS → CPU) and shows the
result in the status bar.

### Step 4: enable AI voice conversion (optional but recommended)

```bash
uv sync --extra ai
```

Import a character model (step 5) and use `engine: rvc-hub` in the preset (see
`examples/presets/ai-voice-rvc-hub.yaml`). The first conversion downloads base
inference assets (hubert/rmvpe) from HuggingFace; set
`HF_ENDPOINT=https://hf-mirror.com` when the network requires it. The vendored
in-process engine (`engine: rvc`) remains available via
`python scripts/fetch_rvc.py`, which records the pinned commit.

When upstream RVC needs its own Python environment (common on Windows), use the
client/server mode instead: run `vivoice serve` on the machine that has the RVC
environment, then use `examples/presets/ai-voice-http.yaml` with your model name
and server address. See
<https://github.com/VIvoice/VIvoice/blob/main/docs/RVC_SERVER_PROTOCOL.md>.

### Step 5: import a voice model

Local import:

```bash
vivoice model add path/to/model.pth --name my-character --index path/to/model.index
```

Download from HuggingFace:

```bash
vivoice model pull <repo-id, e.g. wok000/vcclient000>
```

For large community repositories, download only the files you need:

```bash
vivoice model pull chaye741/RVC-Voice-Models \
  --path "weights/卡通-懒羊羊.pth" --index "indices/卡通-懒羊羊.index"
```

Models live under `~/.vivoice/models/` and are managed on the GUI "Models" page.

Model discovery links:

- Hugging Face: <https://huggingface.co/>
- voice-models.com: <https://voice-models.com/>
- Weights: <https://www.weights.gg/>

Only clone voices you have informed consent to use, and respect each model's
license. See [ETHICS.md](../ETHICS.md).

### Step 6: pick a preset and convert

On the "Convert" page choose an input file (WAV/FLAC/OGG), an output path, and a
preset (`robot`, `pitch-up`, `deep-voice`), then press start. Conversion runs on
a worker thread so the UI stays responsive.

CLI equivalent:

```bash
vivoice process input.wav output.wav --preset examples/presets/robot.yaml
vivoice effects
vivoice devices
```

### Step 7: real-time (future milestone)

Since v0.2, effects marked `[streaming]` (gain/robot/echo/eq/noise-gate/reverb)
can be previewed in real time:

```bash
uv sync --extra realtime
vivoice stream --preset examples/presets/broadcast.yaml
vivoice stream --list-devices
```

The GUI "Live" page offers the same real-time preview with device, sample-rate,
and block-size selectors.
Press `Ctrl+C` to stop. Pitch shift and AI voice conversion are offline-only for
now; the full real-time path (including those effects) is planned for v1 (see
[ROADMAP.md](ROADMAP.md)). On Windows, microphone → processing → other apps
routing uses a virtual cable:

- VB-Cable (freeware, closed source): <https://vb-audio.com/Cable/>

Latency targets: DSP chain under 50 ms; AI conversion labeled with its measured
latency (reference implementations are around 150–200 ms end to end).

### Troubleshooting

- **Status bar says CPU**: no CUDA device was found. Check NVIDIA drivers
  (<https://www.nvidia.com/drivers/>) or run `vivoice devices`.
- **RVC engine not found**: run step 4's `uv sync --extra ai` and
  `python scripts/fetch_rvc.py`.
- **Model download fails**: check HuggingFace connectivity; set the
  `HF_ENDPOINT` environment variable to use a mirror if needed.

### Reference links

- Official RVC repository: <https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI>
- VIvoice architecture: <https://github.com/VIvoice/VIvoice/blob/main/docs/ARCHITECTURE.md>
- VIvoice roadmap: <https://github.com/VIvoice/VIvoice/blob/main/docs/ROADMAP.md>
- Licenses and third parties: <https://github.com/VIvoice/VIvoice/blob/main/THIRD_PARTY_NOTICES.md>
