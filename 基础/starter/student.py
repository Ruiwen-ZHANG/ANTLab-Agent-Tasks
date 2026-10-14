"""待候选人实现。避免读取dev_answers或题号/condition来构造答案。"""
import re

def prepare_messages(question, passages):
    """返回 [{"role":"system|user", "content":"..."}, ...]。
    passages仅含id/source/text，不包含答案或条件标记。
    必须请求JSON对象: {"answer": "简短答案", "citations": ["P..."]}。
    prompt需由本人设计、核查、解释。"""

    rules = """
    1. 角色：你是记录核对员，只能根据下面提供的段落回答，不能使用外部知识。
    2. 找主记录：资料中可能有项目、版本、月份相同，但批次、组别、指标口径或签署状态不同的相近记录。你必须逐项核对问题中的限定条件（项目、版本、月份、批次或组别），先找到全部吻合的主记录。
    3. 关联补充页：其他段落如果没有写项目名，但通过同一个批次代号或编号能明确关联到主记录，也可以作为依据。
    4. 指标对应：问题中的指标名称可能与资料用词不同，要按含义对应，不要因为字面不同就判定证据不足。如果所问指标没有直接写出数值，但关联记录给出了可以计算它的分子和分母，就计算出结果。
    5. 跨段引用：答案用到了哪些段落（包括计算用到的每一段），citations 就列出哪些段落。
    6. 证据不足：只有当资料确实缺少回答所需的信息时，answer 才写"证据不足"，citations 只填最接近问题、但缺少关键信息的一两段。不要编造。
    7. 引用格式：citations 中只填方括号里的段落编号本身（形如 "P123456"），必须原样照抄，不要加任何前缀、来源或其他文字。
    8. 输出格式：只输出一个json对象，不要输出任何其他文字。格式示例：
    {"answer": "简短答案", "citations": ["P123456", "P654321"]}
    answer 必须遵守问题中的格式要求（例如"只输出百分数"只写如 "50%"）。
    """


    blocks = []  # 先准备一个空列表
    for p in passages:  # 按原顺序逐个取出
        block = f"[{p['id']}|来源：{p['source']}]\n{p['text']}"
        blocks.append(block)  # 每个都拼成一段文字，加进列表

    text = "\n\n".join(blocks)  # 每两段之间插入一个空行

    user_content = f"问题：{question}\n\n以下是全部资料段落：\n\n{text}"

    return [
        {"role": "system", "content": rules},
        {"role": "user", "content": user_content},
    ]


def improve(question, passages):
    """返回重新组织/选择的原段落列表，不能修改id/source/text或使用答案标签。
    默认恒等映射仅用于联通，不算已完成改进。可自行扩展结构/调用，须披露与记录。"""

    pattern = r'[\u4e00-\u9fff]{2}项目|R\d+|\d{4}-\d{2}'
    terms = re.findall(pattern, question)

    rest = re.sub(pattern, ' ', question)
    rest = re.split('[？?]', rest)[0]

    grams = set()
    for i in range(len(rest) - 1):
        g = rest[i:i+2]
        if ' ' not in g:
            grams.add(g)

    scored = []
    for p in passages:
        head = re.split('[。；]', p['text'])[0]
        hard = sum(t in p['text'] for t in terms)
        clue = sum(g in head for g in grams)
        scored.append((hard, clue, p))

    print([(h, c, p['id']) for h, c, p in scored])
    return passages