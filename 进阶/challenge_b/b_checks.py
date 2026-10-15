"""B 题检查脚本（离线重放，不调用任何模型）：复现 → 区分性干预 → 修复后对照 → 回归 → 等价变体 → 边界。
每项检查都写明"预期及依据"，再记录"实际"，比较后给出 PASS/FAIL；不只检查返回 200。
原样机 challenge.Engine 不做任何修改；修复版见 fixed_engine.py。
结果写入 仓库根/results/b/b_checks.json，并打印汇总表。
用法（在仓库根目录）：python 进阶/challenge_b/b_checks.py"""
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                           # 仓库根目录
sys.path.insert(0, str(HERE))
from challenge import Engine as OriginalEngine                   # noqa: E402  原样机（基线）
from fixed_engine import CacheKeyFixEngine, FixedEngine           # noqa: E402  修复版

DATA = json.loads((HERE / 'data.json').read_text(encoding='utf-8'))
CORPUS = DATA['corpus']
CASE = {c['id']: c for c in DATA['cases']}

def run_seq(engine_cls, steps, shared=True):
    """按顺序运行若干步。steps 中每项为 (案例ID, 对 request 的改动字典或 None)。
    shared=True 表示所有步骤共用同一个 Engine 实例（缓存状态延续）。"""
    eng = engine_cls(); outs = []
    for cid, change in steps:
        if not shared:
            eng = engine_cls()                                   # 每步新实例 = 清空缓存
        req = copy.deepcopy(CASE[cid]['request'])
        if change:
            req.update(change)
        out = eng.evaluate(req, CORPUS, CASE[cid]['draft'])
        outs.append({'case': cid, 'request': req,
                     'evidence_ids': [e['id'] for e in out['evidence']],
                     'evidence_snapshots': sorted({e['snapshot'] for e in out['evidence']}),
                     'answer': out['answer'], 'locator_status': out['locator_status'],
                     'support_status': out['support_status'], 'cache_hit': out['cache_hit'],
                     'elapsed_ms': round(out['elapsed_ms'], 4), 'run_kind': out['run_kind'],
                     'request_id': out['request_id']})
    return outs

checks = []
def check(cid, kind, title, expect_text, actual, ok):
    checks.append({'id': cid, 'kind': kind, 'title': title, 'expected': expect_text,
                   'actual': actual, 'result': 'PASS' if ok else 'FAIL'})

# ---------- 1. 复现：原样机，R01 → R02 共用实例 ----------
rep = run_seq(OriginalEngine, [('R01', None), ('R02', None)])
r02 = rep[1]
check('B1', '复现', '原样机 R01→R02：R02 请求 v2 却返回 v1 证据',
      '若故障存在：R02 证据为 b01（snapshot v1）、答案为30秒、cache_hit=True',
      rep, r02['evidence_ids'] == ['b01'] and r02['cache_hit'] is True)
check('B1b', '复现-最早边界', 'R02 的证据快照与请求快照不一致（最早出错在缓存查找，检索之前）',
      '请求 snapshot=v2，返回证据 snapshot 应为 v2；故障时为 v1，且 cache_hit=True 说明未进入检索',
      {'request_snapshot': r02['request']['snapshot'], 'evidence_snapshots': r02['evidence_snapshots'],
       'cache_hit': r02['cache_hit']},
      r02['evidence_snapshots'] == ['v1'] and r02['cache_hit'])

# ---------- 2. 区分性干预（解释1：缓存键不含版本；解释2：检索/过滤本身取错版本）----------
fresh = run_seq(OriginalEngine, [('R02', None)])[0]
check('B2', '干预', '原样机新实例单独运行 R02（不经过 R01）',
      '解释1预测：得到 b02/12秒；解释2预测：仍得到 b01',
      fresh, fresh['evidence_ids'] == ['b02'])
reorder = run_seq(OriginalEngine, [('R01', None), ('R02', {'query': 'threshold request timeout'})])[1]
check('B3', '干预', '原样机 R01 后，R02 改用同义词序 "threshold request timeout"（缓存键不同）',
      '解释1预测：键不同→不命中→得到 b02；解释2预测：仍得到 b01',
      reorder, reorder['evidence_ids'] == ['b02'] and reorder['cache_hit'] is False)

# ---------- 3. 反向因果/评价错误：更低耗时来自错误命中缓存 ----------
check('B4', '反向因果', '原样机 R02 的"更快"来自命中旧缓存，而非更好的检索',
      '复现中 R02 cache_hit=True（未进入检索），新实例 cache_hit=False；耗时仅作参考（毫秒级，含波动），快 ≠ 对',
      {'stale_hit_ms': r02['elapsed_ms'], 'stale_cache_hit': r02['cache_hit'],
       'fresh_ms': fresh['elapsed_ms'], 'fresh_cache_hit': fresh['cache_hit']},
      r02['cache_hit'] is True and fresh['cache_hit'] is False)

# ---------- 4. 修复后同条件比较 ----------
fx = run_seq(CacheKeyFixEngine, [('R01', None), ('R02', None)])
check('B5', '修复', '修复版 R01→R02（与 B1 完全相同的输入与顺序）',
      'R02 证据 b02、答案12秒、cache_hit=False',
      fx, fx[1]['evidence_ids'] == ['b02'] and fx[1]['cache_hit'] is False)

# ---------- 5. 回归：原本正常的行为仍成立 ----------
rg1 = run_seq(CacheKeyFixEngine, [('R01', None)])[0]
check('B6', '回归', 'R01 单独运行仍返回 b01、locator valid',
      '与原样机 R01 一致：b01、valid', rg1, rg1['evidence_ids'] == ['b01'] and rg1['locator_status'] == 'valid')
rg2 = run_seq(CacheKeyFixEngine, [('R05', None), ('R06', None)], shared=False)
check('B7', '回归', 'R05、R06 仍返回各自证据且 valid',
      'R05→b05 valid；R06→b06 valid（与原样机一致）', rg2,
      rg2[0]['evidence_ids'] == ['b05'] and rg2[1]['evidence_ids'] == ['b06']
      and all(o['locator_status'] == 'valid' for o in rg2))
rg3 = run_seq(CacheKeyFixEngine, [('R01', None), ('R01', None)])
check('B8', '回归', '完全相同的请求重复两次：缓存仍可复用（spec 第5条允许保留缓存）',
      '第二次 cache_hit=True，证据与第一次相同，request_id 不同', rg3,
      rg3[1]['cache_hit'] is True and rg3[0]['evidence_ids'] == rg3[1]['evidence_ids']
      and rg3[0]['request_id'] != rg3[1]['request_id'])

# ---------- 6. 等价变体 ----------
v1 = run_seq(CacheKeyFixEngine, [('R01', None), ('R02', None)])
v1r = run_seq(CacheKeyFixEngine, [('R02', None), ('R01', None)])
check('B9', '变体-顺序', '修复版颠倒请求顺序 R02→R01，结果与 R01→R02 一致',
      '两种顺序下 R01→b01、R02→b02（资料版本决定结果，与请求先后无关）',
      {'R01_then_R02': v1, 'R02_then_R01': v1r},
      v1[0]['evidence_ids'] == v1r[1]['evidence_ids'] == ['b01']
      and v1[1]['evidence_ids'] == v1r[0]['evidence_ids'] == ['b02'])
v2 = run_seq(CacheKeyFixEngine, [('R01', None), ('R02', {'query': '  Timeout REQUEST threshold '})])[1]
check('B10', '变体-措辞', '修复版 R02 改为大小写与首尾空格不同的等价查询',
      '分词结果相同（strip+lower+split）→ 证据 b02', v2, v2['evidence_ids'] == ['b02'])
v3 = run_seq(CacheKeyFixEngine, [('R01', {'doc_ids': ['alpha', 'beta']}), ('R01', {'doc_ids': ['beta', 'alpha']})])
check('B11', '变体-标识顺序', 'doc_ids 顺序不同（[alpha,beta] vs [beta,alpha]）视为等价',
      '证据相同；第二次命中缓存（键中 doc_ids 已排序）', v3,
      v3[0]['evidence_ids'] == v3[1]['evidence_ids'] and v3[1]['cache_hit'] is True)

# ---------- 7. 边界：登记但本次未修复的问题（预期 FAIL 表示问题仍存在）----------
b3 = run_seq(CacheKeyFixEngine, [('R03', None)])[0]
check('B12', '边界-未修复', 'R03（beta/v1, k=1）：范围外条目占用名额导致漏证据（spec 第2条）',
      '按 spec 应返回 b03；当前先取 top-k 再过滤范围，b01 占掉唯一名额 → 证据为空（问题仍在）',
      b3, b3['evidence_ids'] == ['b03'])
b4 = run_seq(CacheKeyFixEngine, [('R04', None)])[0]
b4f = run_seq(FixedEngine, [('R04', None)])[0]
check('B13', '边界-状态如实化', 'R04：draft 与原文相反（原文"没有测量"），只因 ID 有效就标 supported（spec 第4条）',
      '主修复版仍为 supported（问题仍在）；FixedEngine 无语义检查，改标 not_checked，不再冒充已支持',
      {'CacheKeyFixEngine': b4['support_status'], 'FixedEngine': b4f['support_status']},
      b4f['support_status'] == 'not_checked')
b7 = run_seq(CacheKeyFixEngine, [('R07', None)])[0]
check('B14', '边界-未修复', 'R07（doc_ids=[missing]）：未知文档应返回 invalid_scope（spec 第1条）',
      '按 spec 应有明确 invalid_scope 状态；当前只返回 invalid + not_checked（问题仍在）',
      b7, b7.get('status') == 'invalid_scope')

out_dir = ROOT / 'results' / 'b'; out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / 'b_checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
for c in checks:
    print(f"{c['id']:<4} {c['result']:<4} [{c['kind']}] {c['title']}")
print('详细输入/输出/预期已写入', out_dir / 'b_checks.json')