"""诊断脚本（探索性，不计入 40 次主结果）：
复用某次正式运行记录中【完全相同】的 messages，只在 user 消息末尾追加一句要求：
在 json 中增加 basis 字段，逐条写出核对过程。用来观察模型为什么在规则选择题上回答"证据不足"。
其余设置（模型、参数）与原运行一致，结果保存到 基础/runs_diagnosis/，并标明来源 run_id。
用法（在仓库根目录）：python results/diagnosis/explain_refusal.py <原run_id前缀> [--paid]
不加 --paid 时只打印将要发送的追加内容，不调用模型。"""
import copy, datetime, json, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '基础' / 'starter'))      # 复用题包自带的模型适配层
from provider import call_model                         # noqa: E402

EXTRA = ('\n\n【诊断要求】请在 json 中额外增加 "basis" 字段（放在最前面，不超过 150 字），'
         '逐条写出：你认定的主记录与补页、规则的每个条件、每个候选是否满足、最终结论的理由。')

def main():
    if len(sys.argv) < 2:
        sys.exit('用法：python results/diagnosis/explain_refusal.py <原run_id前缀> [--paid]')
    prefix, paid = sys.argv[1], '--paid' in sys.argv
    src = [p for p in (ROOT / '基础' / 'runs').glob(prefix + '*.json')]
    if len(src) != 1:
        sys.exit(f'按前缀 {prefix} 找到 {len(src)} 个文件，需要恰好 1 个')
    orig = json.loads(src[0].read_text(encoding='utf-8'))
    msgs = copy.deepcopy(orig['messages'])                 # 与原运行完全相同的输入
    msgs[-1]['content'] += EXTRA                           # 唯一改动：追加诊断要求
    config = copy.deepcopy(orig['config'])
    config['parameters']['max_tokens'] = 512               # basis 会变长，放宽输出上限（已披露）
    print('原运行：', orig['run_id'], orig['case_id'], orig['condition'], orig['variant'])
    print('追加内容：', EXTRA.strip())
    if not paid:
        print('（未加 --paid，未调用模型）'); return
    result = call_model(msgs, config)
    record = {'run_kind': 'diagnosis_exploration', 'run_id': str(uuid.uuid4()),
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_run_id': orig['run_id'], 'case_id': orig['case_id'],
              'condition': orig['condition'], 'variant': orig['variant'],
              'change': '仅在 user 消息末尾追加诊断要求；max_tokens 256→512',
              'config': config, 'messages': msgs, **result}
    out = ROOT / '基础' / 'runs_diagnosis'; out.mkdir(exist_ok=True)
    (out / (record['run_id'] + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        print('模型输出：', result['response']['choices'][0]['message']['content'])
    except (KeyError, TypeError, IndexError):
        print('调用失败：', result.get('status'), result.get('error'))
    print('已保存：', out / (record['run_id'] + '.json'))

if __name__ == '__main__':
    main()