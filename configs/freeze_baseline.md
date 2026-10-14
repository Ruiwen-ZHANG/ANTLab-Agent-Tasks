# 基线冻结记录

- 冻结时间：2026-10-14 17:11（北京时间）
- 提示词版本：v3（基础/starter/student.py）
- student.py SHA256：9a1fa281309fa5ae227a5a47d7ad6e87a3f7b2768a09342d02533d93b7f63d08
- cases.json SHA256：c37cda40ada89a18630dd7be098672f7e942e6f57e6199fe1aa2d6046e2b4961
- 数据版本：basic-context-v1.2
- 模型：deepseek-flash（DeepSeek，OpenAI 兼容接口）
- 参数：temperature 0；max_tokens 256；thinking disabled；response_format json_object；timeout 90s
- 运行命令：python starter/runner.py --split evaluation --condition all --limit 32 --paid --config config.local.json
- 冻结后规则：不再修改 student.py 的 prepare_messages 与配置；之后的任何改动都标为探索
- 开发集接触：仅用 D01–D04 调试；冻结前未运行、未查看任何 T 题的模型输出
- 对应 git tag：freeze-baseline（commit b5da369）