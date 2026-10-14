"""待候选人实现。避免读取dev_answers或题号/condition来构造答案。"""
def prepare_messages(question, passages):
    """返回 [{"role":"system|user", "content":"..."}, ...]。
    passages仅含id/source/text，不包含答案或条件标记。
    必须请求JSON对象: {"answer": "简短答案", "citations": ["P..."]}。
    prompt需由本人设计、核查、解释。"""

    rules = """
角色和任务：你是记录核对员，只能根据下面提供的段落回答。
核对规则：段落里可能会有项目、版本、月份都相同但批次、指标口径或签署状态不同的相近记录。要求你逐项核对问题里的每个限定条件（项目、版本、月份、批次或组别、指标名称），全部吻合的段落才能作为依据。citations 里只能填写资料中给出的段落ID，必须原样照抄。
跨段：如果答案需要计算或比较，你要使用并引用所有参与计算的段落。
证据不足：如果找不到完全吻合的信息，answer 写"证据不足"，citations 填你检查过、能说明"缺什么"的段落。不要编造。
输出格式：只输出一个json对象，不要输出任何其他文字。
格式示例：
{"answer": "简短答案", "citations": ["段落ID1", "段落ID2"]}
answer 必须遵守问题中的格式要求（例如"只输出百分数"）。
"""


    blocks = []  # 先准备一个空列表
    for p in passages:  # 按原顺序逐个取出
        block = f"[段落ID:{p['id']}|来源：{p['source']}]\n{p['text']}"
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
    return passages
