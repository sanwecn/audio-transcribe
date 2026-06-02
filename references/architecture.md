# 技术细节

## 架构

```
录音.mp3
  ├─→ TeleSpeechASR API ─→ 转写文本（方言识别强）
  └─→ ffmpeg 转wav → cam++ 滑动窗口 → embedding → sklearn 聚类 → 说话人标签
                                                    ↓
                                          合并 → 带说话人标签的文本
```

## cam++ 滑动窗口原理

1. 将音频按 3 秒窗口、1 秒步长切片
2. 每个切片提取 192 维 speaker embedding
3. 用 AgglomerativeClustering(n_clusters=2) 聚类
4. 按时间中点将聚类标签映射到 ASR 文本段

## TeleSpeechASR API 格式

```
POST http://<host>:<port>/v1/audio/transcriptions
Authorization: Bearer <key>
Content-Type: multipart/form-data

model: TeleAI/TeleSpeechASR
language: zh
file: <audio binary>
```

返回：`{"text": "转写结果"}`

## 与 FunASR 对比（方言场景）

| 测试句 | FunASR | TeleSpeechASR |
|--------|--------|---------------|
| 去大连没啥事 | 我七大连这个人事 | ✅ 正确 |
| 左手掏右手 | 左手掏右手 | 左手套，右手 |
| 俺就找他 | 又找他 | ✅ 识别方言"俺" |
| 那太客气了 | 你那太客气了 | ✅ 正确 |
