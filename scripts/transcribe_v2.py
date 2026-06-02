#!/usr/bin/env python3
"""TeleSpeechASR 转写 + cam++ 滑动窗口说话人分离"""

import os
import sys
import glob
import time
import json
import subprocess
import numpy as np
import requests
import soundfile as sf
from datetime import datetime

# 配置 - 优先从环境变量读取，其次从 .env 文件
def load_dotenv():
    """简单的 .env 加载，不依赖 python-dotenv"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_dotenv()

ASR_API = os.environ.get("TELE_ASR_API", "http://REDACTED_HOST:PORT/v1/audio/transcriptions")
ASR_KEY = os.environ.get("TELE_ASR_KEY", "")
RATE_LIMIT_DELAY = int(os.environ.get("TELE_ASR_RATE_LIMIT", "2"))
WINDOW_SEC = 3.0
STEP_SEC = 1.0


def convert_to_wav(mp3_path, wav_path):
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", wav_path],
        capture_output=True, check=True,
    )


def transcribe_api(audio_path):
    with open(audio_path, "rb") as f:
        resp = requests.post(
            ASR_API,
            headers={"Authorization": f"Bearer {ASR_KEY}"},
            files={"file": (os.path.basename(audio_path), f, "audio/mpeg")},
            data={"model": "TeleAI/TeleSpeechASR", "language": "zh"},
            timeout=120,
        )
    resp.raise_for_status()
    return resp.json()["text"]


def extract_speaker_labels(wav_path, spk_model):
    """滑动窗口提取 embedding，聚类成2个说话人"""
    from sklearn.cluster import AgglomerativeClustering

    audio_data, sr = sf.read(wav_path)
    total = len(audio_data) / sr

    embeddings = []
    centers = []
    t = 0.0
    while t + WINDOW_SEC <= total:
        s = int(t * sr)
        e = int((t + WINDOW_SEC) * sr)
        chunk = audio_data[s:e]
        sf.write("/tmp/_chunk.wav", chunk, sr)
        res = spk_model.generate(input="/tmp/_chunk.wav")
        if res and "spk_embedding" in res[0]:
            embeddings.append(np.array(res[0]["spk_embedding"]))
            centers.append(t + WINDOW_SEC / 2)
        t += STEP_SEC

    if len(embeddings) < 2:
        return None

    emb_matrix = np.vstack(embeddings)
    labels = AgglomerativeClustering(n_clusters=2).fit_predict(emb_matrix)
    return list(zip(centers, labels))


def map_text_to_speakers(text, speaker_timeline):
    """按字符比例将 ASR 文本映射到说话人"""
    import re

    # 按标点分句
    parts = re.split(r"([，。！？、；：])", text)
    merged = []
    for p in parts:
        if not p:
            continue
        if p in "，。！？、；：" and merged:
            merged[-1] += p
        else:
            merged.append(p)
    merged = [s.strip() for s in merged if s.strip()]
    if not merged or not speaker_timeline:
        return [{"speaker": "说话人0", "text": text}]

    total_chars = sum(len(s) for s in merged)
    audio_duration = max(c for c, _ in speaker_timeline) + WINDOW_SEC / 2
    t = 0.0
    results = []
    for sent in merged:
        ratio = len(sent) / total_chars if total_chars > 0 else 1 / len(merged)
        dur = ratio * audio_duration
        mid = t + dur / 2

        # 找最近的 speaker
        best_spk = 0
        best_dist = 9999
        for center, label in speaker_timeline:
            d = abs(center - mid)
            if d < best_dist:
                best_dist = d
                best_spk = label

        results.append({"speaker": f"说话人{best_spk}", "text": sent, "time": t})
        t += dur
    return results


def process_file(mp3_path, output_path, spk_model):
    basename = os.path.basename(mp3_path)
    wav_path = "/tmp/_process.wav"

    # 1. TeleSpeechASR 转写
    text = transcribe_api(mp3_path)

    # 2. cam++ 说话人分离
    convert_to_wav(mp3_path, wav_path)
    spk_timeline = extract_speaker_labels(wav_path, spk_model)

    # 3. 合并
    if spk_timeline:
        segments = map_text_to_speakers(text, spk_timeline)
    else:
        segments = [{"speaker": "说话人0", "text": text, "time": 0}]

    # 4. 写文件
    lines = [
        f"录音文件: {basename}",
        f"转写时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"{'='*60}",
        "",
    ]
    for seg in segments:
        t = seg["time"]
        m, s = int(t // 60), int(t % 60)
        lines.append(f"[{m:02d}:{s:02d}] {seg['speaker']}: {seg['text']}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    n_spk = len(set(seg["speaker"] for seg in segments))
    return n_spk, len(segments)


if __name__ == "__main__":
    from funasr import AutoModel

    # 输入/输出路径可通过环境变量配置
    audio_dir = ***"TRANSCRIBE_INPUT_DIR", "./input")
    output_dir = os.environ.get("TRANSCRIBE_OUTPUT_DIR", os.path.join(audio_dir, "转写结果"))
    os.makedirs(output_dir, exist_ok=True)

    mp3_files = sorted(glob.glob(os.path.join(audio_dir, "*.mp3")))
    total = len(mp3_files)
    print(f"共 {total} 个文件 | API 限速 {RATE_LIMIT_DELAY}s/次")
    print()

    print("加载 cam++ 说话人模型...")
    spk_model = AutoModel(
        model="iic/speech_campplus_sv_zh-cn_16k-common",
        device="cpu",
        disable_update=True,
    )
    print("模型就绪\n")

    for i, mp3 in enumerate(mp3_files, 1):
        basename = os.path.splitext(os.path.basename(mp3))[0]
        output_path = os.path.join(output_dir, basename + ".txt")

        if os.path.exists(output_path):
            print(f"[{i}/{total}] 跳过（已存在）")
            continue

        size_kb = os.path.getsize(mp3) / 1024
        print(f"[{i}/{total}] {basename[:45]} ({size_kb:.0f}KB) ", end="", flush=True)

        try:
            spk_count, line_count = process_file(mp3, output_path, spk_model)
            tag = "✓" if spk_count >= 2 else "⚠仅1人"
            print(f"{tag} 说话人:{spk_count} 行:{line_count}")
        except Exception as e:
            print(f"✗ {e}")

        if i < total:
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n完成！输出: {output_dir}")
