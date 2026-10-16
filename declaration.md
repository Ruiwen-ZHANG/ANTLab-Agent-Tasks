# AI 使用与贡献声明

**真实 API 模型名称**：DeepSeek `deepseek-flash`（非思考模式）

**Token 消耗量级（可选）**：<10 万（单次请求输入约 1,900 token、输出约 20–50 token；全部调用约百余次）

**AI 工具与主要用途**：Claude（Anthropic，经 claude.ai）
- 阅读题包并推荐进阶选 B；梳理 Lost in the Middle 论文要点；起草 notes.md 阅读笔记与事前预测初稿（本人修改后提交，早于首次 API 调用）
- 查阅 DeepSeek 官方文档，指出思考模式默认开启并建议关闭
- 指导并修正本人编写的 `prepare_messages`（v1→v3 的问题分析与措辞建议）与 `improve`（第 1–3、5–8 步代码由 Claude 修正：变量未保存、or/and 混用、return 缩进进循环等）
- **编写**：`results/variant/remap_check.py`、`进阶/challenge_b/fixed_engine.py`、`b_checks.py`、`server_compare.py`、`compare.html`
- 起草 report.md、README.md、decisions.md 部分条目与本声明

**本人核验并承担的关键判断及核验方法**
- 正式题参考答案：逐题对照 `cases.json` 原文核对推理【核对结果：全部同意 / 修改了 Txx——待填】
- 论文数字：亲自在论文 §2 核对 75.8%、53.8%、56.1%
- 思考模式默认开启：亲自阅读 DeepSeek 文档，连通性测试中 `reasoning_content` 为空
- 随机性检查：亲自运行 D01 R1 三次并比对 student hash
- improve 行为：本地运行离线排序与 ID 重映射检查，结果与预测一致
- B 题根因：理解并能解释 `challenge.py` 第 13 行缓存键缺少 snapshot；运行 b_checks.py 与对照页面确认
- 判分口径：审阅 score.py 的四个判定（格式、答案、可定位、证据覆盖）及分母规则

**未实现、未运行或未验证的内容**
- 语义支持仅人工规则近似，未做 NLI/模型裁判
- 参考答案未经独立第三方标注
- 诊断只覆盖 2 个案例、各 1 次
- 未测试思考模式或逐候选结构化核对能否修复规则题
- B 题 R03（范围外条目占名额）、R07（invalid_scope）未修复；多用户/多 worker 行为未测试
- 截止前未做演示视频

**开源/骨架/他人贡献**：题包骨架 `基础/starter/`（runner/provider/server/index.html/lexical/export_runs）与 `进阶/challenge_b/` 原样机来自上游 commit `b028d90`，未修改（除 `student.py`）。

**本人能解释的模块 / 尚未完全理解的模块**：能解释 prepare_messages、improve、判分口径、B 题缓存键根因与修复；对 server_compare.py 的 HTTP 处理细节与 compare.html 的前端渲染理解有限。

**重放/模拟清单**：B 题全部为 offline_replay（耗时为本地函数时间）；基础题 dry-run 记录（mode=dry）只用于检查输入，不计入结果。

**开发/评测接触及冻结后的改动**：提示词与改进方法均只在 D01–D04 上调试；冻结后未修改 prepare_messages/improve；冻结后新增的只有判分、诊断、变体脚本与 B 题代码。

本人确认以上按实际情况填写。
姓名：Ruiwen ZHANG　日期：2026-10-16