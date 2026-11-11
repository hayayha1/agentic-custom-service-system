# -*- coding: utf-8 -*-
import json
import os
from pathlib import Path

out_dir = Path(__file__).resolve().parents[3] / "data" / "evaluation"
src_path = out_dir / "test_dataset.json"

with open(src_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 仅保留纯问题文本列表
pure_questions = [item["question"] for item in data]

# 1. 纯字符串数组 JSON (直接用于自动化脚本遍历: for q in questions: ...)
with open(os.path.join(out_dir, "test_questions_only.json"), "w", encoding="utf-8") as f:
    json.dump(pure_questions, f, ensure_ascii=False, indent=2)

# 2. 纯文本 TXT (每行一个问题，无任何标签干扰，可直接导入测试工具或按行读取)
with open(os.path.join(out_dir, "test_questions_only.txt"), "w", encoding="utf-8") as f:
    for q in pure_questions:
        f.write(f"{q}\n")

# 3. 干净 Markdown 编号列表 (无任何分类与类型标签)
with open(os.path.join(out_dir, "test_questions_only.md"), "w", encoding="utf-8") as f:
    f.write("# 电商客户真实提问测试集 (50 题)\n\n")
    f.write("> 纯真实用户问句，无分类、无标注、无答案，直接用于对话框输入测试或自动化批处理。\n\n")
    for idx, q in enumerate(pure_questions, 1):
        f.write(f"{idx}. {q}\n")

print(f"Updated test questions: total {len(pure_questions)} pure questions.")
