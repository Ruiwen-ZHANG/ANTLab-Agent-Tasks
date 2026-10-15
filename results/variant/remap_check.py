"""变体检查（不调用模型）：ID 重映射 + 顺序打乱，检查 improve() 是否只按内容工作。
做法：对每道题的 R0 段落
  1. 把所有段落 ID 换成新的随机 ID（如 X000017），原文和来源不变 → "ID 重映射"
  2. 再用固定随机种子打乱段落顺序 → "顺序变体"
  3. 分别运行 improve()，把输出顺序映射回原 ID，与原始 R0 的 improve() 输出比较
预测（运行前写在 notes.md）：ID 重映射后输出顺序应完全相同；
  顺序打乱后，前两段（主记录+补页）应相同，平局题（如 D02）可能不同。
同时检查 prepare_messages 的输出里只出现新 ID、不出现旧 ID（说明没有按固定 ID 生成）。
用法（在仓库根目录）：python results/variant/remap_check.py"""
import copy, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '基础' / 'starter'))
import student                                                   # noqa: E402  被检查的 improve / prepare_messages

cases = json.loads((ROOT / '基础/data/cases.json').read_text(encoding='utf-8'))
rng = random.Random(20261015)                                     # 固定种子，结果可复现
rows, all_ok = [], True
for c in cases:
    by_id = {p['id']: p for p in c['passages']}
    r0 = [copy.deepcopy(by_id[i]) for i in c['conditions']['R0']]
    base = [p['id'] for p in student.improve(c['question'], copy.deepcopy(r0))]   # 原始 R0 的改进顺序

    # 1) ID 重映射：新 ID → 旧 ID 的对照表
    new_of = {p['id']: f'X{rng.randrange(10**6):06d}' for p in r0}
    old_of = {v: k for k, v in new_of.items()}
    remapped = [dict(p, id=new_of[p['id']]) for p in r0]
    out_remap = [old_of[p['id']] for p in student.improve(c['question'], copy.deepcopy(remapped))]

    # 2) 在重映射基础上再打乱顺序
    shuffled = copy.deepcopy(remapped); rng.shuffle(shuffled)
    out_shuf = [old_of[p['id']] for p in student.improve(c['question'], copy.deepcopy(shuffled))]

    # 3) prepare_messages 只应出现新 ID
    text = ''.join(m['content'] for m in student.prepare_messages(c['question'], copy.deepcopy(remapped)))
    leak = [i for i in new_of if i in text]                       # 旧 ID 泄漏
    same_remap = out_remap == base
    same_top2 = out_shuf[:2] == base[:2]
    all_ok &= same_remap and not leak
    rows.append((c['id'], same_remap, same_top2, out_shuf == base, len(leak)))
    print(f"{c['id']}  ID重映射后顺序相同={same_remap}  打乱后前两段相同={same_top2}  "
          f"打乱后全顺序相同={out_shuf == base}  旧ID泄漏={len(leak)}  原前两段={base[:2]}  打乱后前两段={out_shuf[:2]}")

out = ROOT / 'results' / 'variant' / 'remap_check_result.json'
out.write_text(json.dumps({'seed': 20261015, 'student_sha_note': '运行时的 基础/starter/student.py',
                           'rows': [dict(zip(['case', 'same_after_remap', 'same_top2_after_shuffle',
                                              'same_full_after_shuffle', 'old_id_leaks'], r)) for r in rows]},
                          ensure_ascii=False, indent=2), encoding='utf-8')
print('全部题 ID 重映射不变且无旧 ID 泄漏：', all_ok, '；结果已保存', out)