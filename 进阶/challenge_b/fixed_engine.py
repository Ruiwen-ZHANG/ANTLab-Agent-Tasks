"""B 题修复版 Engine（原样机 challenge.py 保持不动，作为基线）。
主问题：换了资料版本（snapshot）却显示旧结论 —— R01(alpha/v1) 之后运行 R02(alpha/v2)，R02 返回 v1 的证据与旧答案。
根因（已由区分性干预确认，见 results/b/）：原 Engine 的缓存键只有 query 文本，
  key = request['query'].strip().lower()，没有包含 doc_ids / snapshot / k / draft，
  因此"查询词相同、资料版本不同"的请求会命中上一个请求的缓存结果。
最小修复：缓存键改为包含所有会影响结果的输入。其余逻辑与原样机逐行一致，便于对照。
被舍弃的替代：完全关闭缓存（也能消除症状，但丢掉了"等价输入复用结果"的能力，spec 第5条允许保留缓存）。

CacheKeyFixEngine：只修缓存键（主修复，用于修复前后同条件比较）
FixedEngine：在主修复之外，把"仅 ID 有效"时的 support_status 从 supported 改为 not_checked
  （本实现没有语义检查，按 spec 第4条如实标注；这是第二处独立改动，单独报告，不混入主修复的因果结论）"""
import copy
import json
import time
import uuid


class CacheKeyFixEngine:
    def __init__(self):
        self.cache = {}

    @staticmethod
    def cache_key(request, draft):
        """缓存键：所有会影响输出的输入都要包含在内"""
        return json.dumps({
            'query': request['query'].strip().lower(),          # 与原样机相同的查询规范化
            'doc_ids': sorted(request['doc_ids']),               # 文档范围（排序后，doc_ids 顺序不同视为等价）
            'snapshot': request['snapshot'],                     # 资料版本 —— 原样机缺少这一项，是主故障根因
            'k': request['k'],                                   # 返回条数
            'draft': {'answer': draft['answer'], 'citations': draft['citations']},  # 待查证的回答
        }, ensure_ascii=False, sort_keys=True)

    def support(self, valid):
        """支持状态判定：主修复版保持原样机行为（ID 有效即 supported），以隔离缓存修复的效果"""
        return 'supported' if valid else 'not_checked'

    def evaluate(self, request, corpus, draft):
        started = time.perf_counter()
        key = self.cache_key(request, draft)                     # ← 唯一改动（原：request['query'].strip().lower()）
        hit = key in self.cache
        if hit:
            result = copy.deepcopy(self.cache[key])
        else:
            terms = set(request['query'].strip().lower().split())
            ranked = sorted(corpus, key=lambda b: (-len(terms & set(b['tags'])), b['id']))
            selected = [b for b in ranked[:request['k']] if terms & set(b['tags'])]
            evidence = [b for b in selected if b['doc_id'] in request['doc_ids'] and b['snapshot'] == request['snapshot']]
            citations = draft['citations']
            valid = bool(citations) and set(citations).issubset({b['id'] for b in evidence})
            result = {'answer': draft['answer'], 'citations': citations, 'evidence': evidence,
                      'locator_status': 'valid' if valid else 'invalid',
                      'support_status': self.support(valid),
                      'judgment_source': 'rule', 'status': 'ok'}
            self.cache[key] = copy.deepcopy(result)
        result.update(request_id=str(uuid.uuid4()), request=copy.deepcopy(request), cache_hit=hit,
                      elapsed_ms=(time.perf_counter()-started)*1000, run_kind='offline_replay')
        return result


class FixedEngine(CacheKeyFixEngine):
    def support(self, valid):
        """没有实现语义检查：ID 有效也只能标 not_checked（spec 第4条），不再把“可定位”冒充“已支持”"""
        return 'not_checked'