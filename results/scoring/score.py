"""判分脚本：读取 基础/runs/ 中的真实调用记录，与参考答案比对，输出逐例表 results/results.csv。
参考答案来源：
  - 开发题 D01–D04：题包 基础/data/dev_answers.json（官方参考）
  - 正式题 T01–T08：results/scoring/gold_eval_self.json（本人阅读原文标注，未经独立标注）
判分口径（规则判分，judgment_source=rule）：
  1. format_ok      ：模型输出能解析为含 answer(字符串) 和 citations(列表) 的 JSON
  2. answer_correct ：answer 规范化后与参考答案或其别名完全一致（去空白、全角%→%、去末尾"秒"）
  3. citation_valid ：citations 非空，且每个 ID 都在本次实际输入的 selected_passage_ids 中
  4. evidence_cover ：参考证据 ID 全部出现在 citations 中；参考答案为"证据不足"时记为 NA
  语义支持（引用原文是否真的支持结论）不由本脚本判断，见 results/scoring/人工核查.md
分母：所有真实调用（mode=paid）的首次尝试均计入，技术失败与格式错误记为不正确，不删除。
用法（在仓库根目录）：python results/scoring/score.py"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]                     # 仓库根目录
RUNS = ROOT / '基础' / 'runs'                                   # 运行记录目录
OUT = ROOT / 'results' / 'results.csv'                         # 逐例结果输出

def load_gold():
    """合并开发题官方答案与正式题本人标注，返回 {题号: 参考答案字典}"""
    gold = {}
    for g in json.loads((ROOT / '基础/data/dev_answers.json').read_text(encoding='utf-8')):
        gold[g['id']] = dict(g, gold_source='official_dev')    # 开发题：官方参考
    path = ROOT / 'results/scoring/gold_eval_self.json'
    if path.exists():
        for g in json.loads(path.read_text(encoding='utf-8')):
            gold[g['id']] = dict(g, gold_source='self_annotated')  # 正式题：本人标注
    return gold

def norm(s):
    """答案规范化：去空白、全角百分号转半角、去掉末尾的"秒"字"""
    s = re.sub(r'\s+', '', str(s)).replace('％', '%')
    return s[:-1] if s.endswith('秒') else s

def parse(record):
    """从运行记录中取出模型输出文本，并尝试解析为 JSON；返回 (原文, 解析结果或None)"""
    try:
        content = record['response']['choices'][0]['message']['content']
    except (KeyError, TypeError, IndexError):
        return '', None                                       # 技术失败：没有响应内容
    try:
        obj = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return content, None                                  # 格式错误：不是合法 JSON
    if not isinstance(obj, dict) or not isinstance(obj.get('answer'), str) or not isinstance(obj.get('citations'), list):
        return content, None                                  # 字段缺失或类型不对
    return content, obj

def main():
    gold = load_gold()
    records = [json.loads(p.read_text(encoding='utf-8')) for p in RUNS.glob('*.json')]
    records = [r for r in records if r.get('mode') == 'paid']  # 只统计真实调用；dry/mock 不计
    records.sort(key=lambda r: r['utc'])                       # 按时间排序，用于区分首次/重试

    seen = {}                                                  # (题号,条件,版本,student哈希) → 已出现次数
    rows = []
    for r in records:
        key = (r['case_id'], r['condition'], r['variant'], r['student_sha256'])
        seen[key] = seen.get(key, 0) + 1
        content, obj = parse(r)
        g = gold.get(r['case_id'])
        row = {
            'run_id': r['run_id'], 'case_id': r['case_id'], 'split': r['split'],
            'condition': r['condition'], 'variant': r['variant'],
            'attempt': 'first' if seen[key] == 1 else f'repeat{seen[key]}',   # 同一配置第几次运行
            'student_sha8': r['student_sha256'][:8],
            'api_status': r['status'], 'elapsed_seconds': r.get('elapsed_seconds'),
            'prompt_tokens': (r.get('usage') or {}).get('prompt_tokens'),
            'completion_tokens': (r.get('usage') or {}).get('completion_tokens'),
            'usage_source': 'provider_usage_field' if r.get('usage') else 'missing',
            'model_output': content,
            'answer': obj['answer'] if obj else '', 'citations': ';'.join(map(str, obj['citations'])) if obj else '',
            'gold_answer': g['answer'] if g else '', 'gold_evidence': ';'.join(g['evidence_ids']) if g else '',
            'gold_source': g['gold_source'] if g else 'none',
            'format_ok': obj is not None,
        }
        if obj is None or g is None:                           # 失败或无参考答案：判为不正确/无法判
            row.update(answer_correct=False if g else 'NA', citation_valid=False, evidence_cover='NA' if not g else False,
                       judgment_source='rule', reason='技术失败或格式错误' if obj is None else '无参考答案')
        else:
            allowed = {norm(a) for a in [g['answer']] + g.get('aliases', [])}
            cited = [str(c) for c in obj['citations']]
            row['answer_correct'] = norm(obj['answer']) in allowed
            row['citation_valid'] = bool(cited) and all(c in r['selected_passage_ids'] for c in cited)
            row['evidence_cover'] = 'NA' if not g['evidence_ids'] else set(g['evidence_ids']) <= set(cited)
            row['judgment_source'] = 'rule'
            row['reason'] = g.get('reason', '')
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:    # utf-8-sig 方便 Excel 直接打开中文
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # 汇总：只统计正式题的首次尝试（主结果），按 条件+版本 分组
    print('正式题主结果（首次尝试）：条件/版本  答对/总数  引用可定位  证据覆盖(适用题)  耗时中位数')
    groups = {}
    for row in rows:
        if row['split'] == 'evaluation' and row['attempt'] == 'first':
            groups.setdefault((row['condition'], row['variant']), []).append(row)
    for (cond, var), rs in sorted(groups.items()):
        n = len(rs)
        ok = sum(r['answer_correct'] is True for r in rs)
        loc = sum(r['citation_valid'] is True for r in rs)
        cov_rows = [r for r in rs if r['evidence_cover'] != 'NA']
        cov = sum(r['evidence_cover'] is True for r in cov_rows)
        ts = sorted(r['elapsed_seconds'] for r in rs if r['elapsed_seconds'] is not None)
        med = ts[len(ts) // 2] if ts else None
        print(f'  {cond:>2} {var:<8}  {ok}/{n}  {loc}/{n}  {cov}/{len(cov_rows)}  {med:.2f}s' if med else f'  {cond} {var} {ok}/{n}')
    print(f'逐例表已写入 {OUT}')

if __name__ == '__main__':
    main()