# 🎙️ 录音转文字

> 免费、本地部署、支持方言的录音转文字方案

## ✨ 特点

- 🆓 **完全免费** — 模型开源，API 可用免费额度
- 🗣️ **方言识别** — 业内首个支持普通话+英文+50种方言自由混说的语音识别大模型
- 👥 **说话人分离** — 自动区分两个说话人，输出带标签的对话文本
- 🏠 **本地部署** — 所有模型可完全离线运行，数据不出内网
- 📝 **带时间戳** — 每句话标注时间位置，方便回溯

## 🗺️ 支持的方言

TeleSpeechASR 支持粤语、上海话、四川话、河南话、东北话、闽南话等 50+ 种方言，以及中英文自由混说。

| 方言 | 支持 |
|------|------|
| 普通话 | ✅ |
| 粤语 | ✅ |
| 上海话 | ✅ |
| 四川话 | ✅ |
| 河南话 | ✅ |
| 东北话 | ✅ |
| 闽南话 | ✅ |
| 英文 | ✅ |
| 中英混说 | ✅ |
| 其他 40+ 方言 | ✅ |

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/sanwecn/call-transcribe.git
cd call-transcribe
```

### 2. 创建 Python 环境

```bash
uv venv funasr-env --python 3.11
uv pip install -p funasr-env/bin/python funasr torch torchaudio soundfile scikit-learn requests
```

### 3. 配置 API

TeleSpeechASR 有两种使用方式：

**方式一：SiliconFlow 免费 API（推荐）**

注册 [SiliconFlow](https://siliconflow.cn) 账号，获取免费 API Key。

```bash
cp .env.example .env
# 编辑 .env，填入：
# TELE_ASR_API=https://api.siliconflow.cn/v1/audio/transcriptions
# TELE_ASR_KEY=sk-xxx
```

**方式二：本地部署**

使用 vLLM 在本地部署 TeleSpeechASR 模型：

```bash
vllm serve TeleAI/TeleSpeechASR --port 8000
```

```bash
# .env 中配置：
# TELE_ASR_API=http://localhost:8000/v1/audio/transcriptions
# TELE_ASR_KEY=local
```

### 4. 运行

```bash
# 将录音文件放入 input/ 目录
mkdir -p input
cp /path/to/*.mp3 input/

# 运行转写
./funasr-env/bin/python scripts/transcribe_v2.py
```

结果输出到 `output/` 目录。

## 📄 输出格式

```
录音文件: example.mp3
转写时间: 2026-06-02 20:37:18
============================================================

[00:00] 说话人1: 喂，你好，
[00:02] 说话人0: 有什么事吗？
[00:04] 说话人0: 你这搞的什么名堂？
[00:07] 说话人1: 我有事儿，那个地方的钱现在怎么处理的？
```

## 🔧 技术方案

```
录音.mp3
  ├─→ TeleSpeechASR API ─→ 转写文本（方言识别）
  └─→ cam++ 滑动窗口 ─→ speaker embedding ─→ 聚类 ─→ 说话人标签
                                                      ↓
                                            合并 → 带标签的文本
```

- **ASR**：[TeleSpeechASR](https://modelscope.cn/models/TeleAI/TeleSpeechASR) — 业内首个普通话+英文+50方言自由混说模型
- **说话人分离**：[cam++](https://modelscope.cn/models/iic/speech_campplus_sv_zh-cn_16k-common) 滑动窗口 + sklearn 聚类
- **模型来源**：全部从 [ModelScope](https://modelscope.cn) 自动下载，无需 HuggingFace token

## 📊 质量实测（92 个录音文件）

| 指标 | 结果 |
|------|------|
| ✅ 说话人分离成功 | 85 个（96.6%） |
| ⚠️ 仅识别 1 人 | 3 个（3.4%，<10秒短录音） |
| 方言识别准确率 | 显著优于 Whisper/FunASR |

## ⚠️ 已知限制

- 仅支持两人对话（多人会议不适用）
- 极短录音（<10秒）说话人分离可能失败
- 说话人标签（0/1）不固定，每次运行可能互换
- cam++ embedding 提取在 CPU 上较慢（每文件约 20-40 秒）

## 📁 项目结构

```
call-transcribe/
├── SKILL.md                      # 技能描述
├── README.md                     # 本文件
├── .env.example                  # 配置模板
├── .gitignore                    # Git 忽略规则
├── scripts/
│   ├── transcribe_v2.py          # 主脚本：转写 + 说话人分离
│   └── merge_speakers.py         # 后处理：多余说话人标签合并
└── references/
    └── architecture.md           # 技术细节
```

## 📬 联系作者

- Twitter: [@sanwe](https://x.com/sanwe)

## 📄 License

MIT
