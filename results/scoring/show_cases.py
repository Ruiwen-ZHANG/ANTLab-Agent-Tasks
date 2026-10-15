"""阅读辅助：打印每道正式题的问题，以及 7 段资料各自的第一句（关键事实都在第一句）。
只读取公开输入 cases.json，不读取任何运行结果；用于本人标注参考答案。
用法（在仓库根目录）：python results/scoring/show_cases.py [题号...]"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # 仓库根目录（本文件在 results/scoring/ 下）
cases = json.loads((ROOT / '基础/data/cases.json').read_text(encoding='utf-8'))
wanted = set(sys.argv[1:])                          # 命令行可指定题号，如 T01 T02；不指定则打印全部正式题

for c in cases:
    if c['split'] != 'evaluation':
        continue
    if wanted and c['id'] not in wanted:
        continue
    print(f"\n=== {c['id']} {c['question']}")
    for p in c['passages']:
        first = re.split('。', p['text'])[0]
        print(f"  {p['id']}  {first}")