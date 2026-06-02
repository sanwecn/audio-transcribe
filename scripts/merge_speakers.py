#!/usr/bin/env python3
"""自动合并多余说话人标签为 0 和 1"""

import os
import re
import glob

def merge_speakers(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 提取所有说话人
    spk_map = {}  # 原始spk -> 目标spk(0或1)
    last_target = -1
    new_lines = []

    for line in lines:
        # 匹配 [时间] 说话人N: 内容
        m = re.match(r'(\[\d{2}:\d{2}-\d{2}:\d{2}\]) 说话人(\d+): (.*)', line)
        if m:
            time_str, spk_id, text = m.group(1), int(m.group(2)), m.group(3)
            if spk_id not in spk_map:
                # 交替分配 0 和 1
                target = 0 if last_target != 0 else 1
                spk_map[spk_id] = target
            last_target = spk_map[spk_id]
            new_lines.append(f"{time_str} 说话人{spk_map[spk_id]}: {text}\n")
        else:
            new_lines.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return len(spk_map)

if __name__ == "__main__":
    output_dir = "./output"
    files = sorted(glob.glob(os.path.join(output_dir, "*.txt")))
    
    fixed = 0
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()
        
        # 统计原始说话人数
        spks = set(re.findall(r'说话人(\d+)', content))
        
        if len(spks) > 2:
            spk_count = merge_speakers(f, f)  # 覆盖原文件
            print(f"✓ 合并 {len(spks)}人→2人: {os.path.basename(f)[:50]}")
            fixed += 1
        elif len(spks) == 2:
            pass  # 完美，跳过
        elif len(spks) == 1:
            print(f"⚠ 仅1人: {os.path.basename(f)[:50]}")
        else:
            print(f"⚠ 无标签: {os.path.basename(f)[:50]}")
    
    print(f"\n共修正 {fixed} 个文件")
