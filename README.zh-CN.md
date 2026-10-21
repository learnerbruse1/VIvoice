# VIvoice

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-informational.svg)](pyproject.toml)
[![CI](https://github.com/VIvoice/VIvoice/actions/workflows/ci.yml/badge.svg)](https://github.com/VIvoice/VIvoice/actions/workflows/ci.yml)

VIvoice 是一个「离线优先、可扩展」的变声器。它把确定性 DSP 效果（音高偏移、机器人声、回声、增益等）
与可插拔的 AI 音色转换层结合。默认 AI 引擎是
[RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)，因此你可以直接导入
社区在 HuggingFace、voice-models.com 等站点分享的 `.pth` / `.index` 角色音色模型。

> English version: [README.md](README.md).

## 为什么选择 VIvoice

- **高扩展性**——效果器和 AI 引擎都是边界清晰的小类。见
  [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md)。
- **高稳定性**——音频核心是纯函数式、有单元测试的管道，没有全局可变状态；GUI 和 CLI 都是同一引擎
  之上的薄前端。
- **本地优先**——全部在本机运行；检测到 NVIDIA CUDA GPU 时自动使用 GPU，否则回落到 CPU。
- **对延迟坦诚**——v0 是离线文件到文件；实时流是规划中的里程碑，延迟目标写在
  [docs/ROADMAP.md](docs/ROADMAP.md)。

## 功能（v0.1）

- 无头引擎 + PySide6 桌面 GUI + `vivoice` 命令行
- 48 kHz float32 处理，DSP 支持多声道
- 内置效果：增益、音高偏移（相位声码器）、机器人（环形调制）、回声、三段 EQ、
  噪声门、混响
- YAML 预设与效果注册表（`vivoice effects`）
- 实时预览（`vivoice stream`）支持实时音高偏移；离线渲染仍使用更高音质的相位声码器
- 分块渲染：内存有界、平滑进度、可随时取消
- 本地音色模型管理（`vivoice model add/list/remove`）与 HuggingFace 下载（`vivoice model pull <repo-id>`）
- 计算设备自动检测：CUDA → MPS → CPU，并支持 `--device` 覆盖
- AI 音色转换：经过验证的 `rvc-hub` 引擎（直接加载社区 RVC `.pth`/`.index` 模型）
  或本地转换服务（`vivoice serve`、`engine: rvc-http`）
- 入口点插件系统与 JSON 参数 Schema（`vivoice schema`、`vivoice effects <类型>`）
- 用户设置（`vivoice config list|get|set`）
- 中英双语 README，应用内置详细使用指南（带步骤与链接）

## 快速开始

环境要求：Python 3.11–3.13 和 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/VIvoice/VIvoice.git
cd VIvoice
uv sync --extra dev --extra realtime
uv run vivoice effects
uv run vivoice-gui
```

启用 AI 音色转换引擎（可选，依赖较大）：

```bash
uv sync --extra ai
uv run vivoice model pull <hf-repo-id> # 或：vivoice model add path/to/model.pth
# 然后使用 ai-voice-rvc-hub 预设（engine: rvc-hub, model: <模型名>）
```

## 命令行速览

```bash
vivoice process input.wav output.wav --preset examples/presets/robot.yaml
vivoice effects                    # 列出已注册效果
vivoice schema                     # 导出 JSON Schema 供工具使用
vivoice devices                    # 显示检测到的计算设备
vivoice model add voice.pth --name alice --index voice.index
vivoice model list
vivoice model pull wok000/vcclient000
vivoice gui                        # 启动桌面应用
vivoice stream --preset examples/presets/broadcast.yaml
vivoice serve --port 7865          # 以 HTTP 暴露 RVC 转换服务
vivoice config set sample_rate 44100
```

完整步骤见 `vivoice --help` 和 [docs/USER_GUIDE.md](docs/USER_GUIDE.md)。

## 文档

- [架构](docs/ARCHITECTURE.md)
- [使用指南（双语）](docs/USER_GUIDE.md)
- [开发效果器与适配器](docs/PLUGIN_DEVELOPMENT.md)
- [预设格式](docs/preset-format.md)
- [路线图](docs/ROADMAP.md)
- [架构决策记录](docs/adr/)
- [术语表](CONTEXT.md)

## 伦理声明

音色转换可能被滥用。克隆任何人的声音前，必须取得对方知情同意。请阅读
[ETHICS.md](ETHICS.md)，切勿将 VIvoice 用于冒充或诈骗。

## 许可证与第三方

VIvoice 采用 [MIT](LICENSE) 许可证。可选的 RVC 适配器以固定 commit 形式引入 MIT 许可证的
[RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)，
详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。你导入的音色模型有其各自的许可证——请遵守。
