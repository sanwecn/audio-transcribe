---
name: call-transcribe
description: "电话录音转文字，支持方言识别 + 说话人分离，输出带时间戳的双人文本。"
---

# 电话录音转文字

将电话录音转为可读文本，自动分离两个说话人。

## 核心方案

- **ASR**：TeleSpeechASR API（方言识别优于 FunASR/Whisper）
- **说话人分离**：FunASR cam++ 滑动窗口 + sklearn 聚类
- **不依赖 HuggingFace token**，全部模型从 ModelScope 下载

## 使用方式

```bash
cd <workspace>
./funasr-env/bin/python scripts/transcribe_v2.py
```

输入：`./input/*.mp3`
输出：`./output/*.txt`

## 输出格式

```
录音文件: xxx.mp3
转写时间: 2026-06-02 20:37:18
============================================================

[00:00] 说话人1: 喂在那边您好，
[00:02] 说话人0: 有什么事吗？
[00:04] 说话人0: 你这搞的什么名堂？
```

## 环境依赖

- Python 3.11 venv：`./funasr-env/`
- `pip install funasr torch soundfile scikit-learn requests`
- ffmpeg（系统已装）
- TeleSpeechASR API 服务

## 部署流程

### 1. 创建 Python 环境

```bash
uv venv funasr-env --python 3.11
uv pip install -p funasr-env/bin/python funasr torch torchaudio soundfile scikit-learn requests
```

### 2. 部署 TeleSpeechASR API

TeleSpeechASR 模型部署在内网服务器 `REDACTED_HOST:PORT`，使用 vLLM 或兼容的 OpenAI API 格式。

启动命令（在 API 服务器上）：
```bash
# 使用 vLLM 部署
vllm serve TeleAI/TeleSpeechASR --port 18000
```

### 3. 配置 API 密钥

复制 `.env.example` 为 `.env` 并填入实际值：

```bash
cp .env.example .env
# 编辑 .env 填入 API 密钥
```

或直接设置环境变量：

```bash
export TELE_ASR_API="http://<IP>:18000/v1/audio/transcriptions"
export TELE_ASR_KEY="<密钥>"
```

脚本优先读取环境变量，其次读取 `.env` 文件。

### 4. 模型自动下载

首次运行时，以下模型自动从 ModelScope 下载（无需 HuggingFace token）：

| 模型 | 用途 | 大小 |
|------|------|------|
| `paraformer-zh` | ASR（备用） | ~950MB |
| `fsmn-vad` | 语音端点检测 | ~2MB |
| `ct-punc` | 标点恢复 | ~1GB |
| `iic/speech_campplus_sv_zh-cn_16k-common` | 说话人 embedding | ~27MB |

缓存目录：`~/.cache/modelscope/`

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 滑动窗口 | 3秒 | cam++ 提取 embedding 的窗口大小 |
| 步长 | 1秒 | 窗口滑动步长 |
| 聚类数 | 2 | 电话录音固定两人 |
| API 限速 | 2秒/次 | 防止 TeleSpeechASR 触发限流 |

## 已知限制

- 仅支持两人对话（多人会议不适用）
- 极短录音（<10秒）说话人分离失败，退化为单人
- 说话人标签（0/1）不固定，每次运行可能互换
- cam++ embedding 提取比 API 调用更耗时（CPU 模式）

## 质量统计（92个文件实测）

- ✅ 2人分离成功：85个（96.6%）
- ⚠️ 仅识别1人：3个（3.4%，均为<10秒短录音）

## 曾尝试的方案（已弃用）

| 方案 | 问题 |
|------|------|
| FunASR 全家桶（paraformer + cam++） | 方言识别差，说话人标签过多（3-11人） |
| pyannote-audio | 需要 HuggingFace token，模型 gated |
| SpeechBrain | 同样需要 HF 认证 |
| TeleSpeechASR 单独使用 | 无说话人分离能力 |
