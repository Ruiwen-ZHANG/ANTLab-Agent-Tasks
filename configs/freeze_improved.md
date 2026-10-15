# 改进版冻结记录
- improve 版本：v1（主记录前置 + 批次代号补页跟随；只重排、不删段）
- student.py SHA256：2018e25d19b0f06153fb055c88e7f6496bf7c19df7b8f63ebc96dc2c619c1208
- prepare_messages：与基线 v3 完全相同
- 模型与参数：与基线相同（见 freeze_baseline.md）
- 运行命令：python starter/runner.py --split evaluation --condition R0 --variant improved --limit 8 --paid --config config.local.json（在 基础 目录下）
- 开发集结果：改进 10/12 vs 基线 9/12；纠正 D01-R2、D04-R1，新错 D04-R0
- 已知局限：分数平局时仍依赖原顺序；证据位置固定后，无关段落顺序仍可导致翻转
- 开发集接触：改进方法仅在 D01–D04 上设计和验证；冻结前未查看任何 T 题输出内容