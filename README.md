# ANTLab Agent 考核作品：基础题 + 进阶 B（系统失效诊断）

- 上游：https://github.com/Shiina413/ANTLab-Agent-Tasks ，源码基点 `b028d90f43f44585cf085a3f607516a94f485e88`
- 最终分支：`main`；最终 commit SHA：内容版本 `f96f9bad8d936abf5cd0e11d8f728752a93e9ba1`（代码、报告、结果均在此版本）；其后仅一次提交只修改本行，收集表登记的是那一次提交（tag: `final-submission`）
- 查看本人全部改动：`git diff b028d90 HEAD --stat`
- 整合报告：[report.md](report.md)；决策：[decisions.md](decisions.md)；声明：[declaration.md](declaration.md)；过程笔记：[notes.md](notes.md)

## 环境
Python 3.10+（本人使用 3.14），只用标准库，无需安装依赖。Windows PowerShell 下测试。

## 复算（离线，不产生费用）
| 目的 | 命令（仓库根目录） | 输出 |
|---|---|---|
| 基础：逐例判分与汇总 | `python results/scoring/score.py` | `results/results.csv` + 终端汇总 |
| 基础：查看正式题原文首句 | `python results/scoring/show_cases.py T01` | 终端 |
| 基础：ID 重映射/顺序变体检查 | `python results/variant/remap_check.py` | `results/variant/remap_check_result.json` |
| B：原样机基线重放 | `python 进阶/challenge_b/run_cases.py --output runs/b/baseline_original.json` | 同名文件 |
| B：修复版重放 | `python 进阶/challenge_b/run_cases.py --engine fixed_engine:FixedEngine --output runs/b/fixed.json` | 同名文件 |
| B：复现/干预/修复/回归/变体/边界 15 项检查 | `python 进阶/challenge_b/b_checks.py` | `results/b/b_checks.json` |
| B：修复前后对照页面 | `cd 进阶/challenge_b; python server_compare.py` → http://127.0.0.1:8767 | 页面 |
| 基础：输入预览（不调用模型） | `cd 基础; python starter/runner.py --case D01 --condition R0 --dry-run --config config.example.json` | `基础/runs/` |

## ⚠ 会产生模型费用的命令（需环境变量 `ASSESSMENT_API_KEY` 与本地 `基础/config.local.json`，均未提交）
```
cd 基础
python starter/runner.py --split evaluation --condition all --limit 32 --paid --config config.local.json        # 32 次基线
python starter/runner.py --split evaluation --condition R0 --variant improved --limit 8 --paid --config config.local.json  # 8 次改进
python starter/server.py --config config.local.json --allow-paid     # 页面真实调用
python results/diagnosis/explain_refusal.py <run_id前缀> --paid      # 诊断（在仓库根目录）
```
`config.local.json` 格式同 `基础/config.example.json`，实际参数见 `configs/freeze_baseline.md` 与每个 run 记录的 `config` 字段。

## 目录
```
基础/starter/student.py        本人实现：prepare_messages（提示词 v3）、improve（证据前置重排 v1）
基础/runs/                     全部真实/预览调用记录（含失败与重复；文件名为 run_id）
基础/runs_diagnosis/           诊断探索调用（不计入主结果）
configs/                       冻结记录（模型、参数、hash、tag）
results/results.csv            逐例结果（run_id、题号、条件、版本、首次/重复、输出、判定、API 状态、耗时、usage 来源）
results/scoring/               判分脚本、正式题参考答案、人工核查规则
results/variant/               ID 重映射检查
results/b/                     B 题检查结果
进阶/challenge_b/              原样机（未修改）+ fixed_engine.py、b_checks.py、server_compare.py、compare.html
runs/b/                        B 题原样机/修复版重放记录
docs/                          页面截图
```

## 完成 / 未完成
| 项 | 状态 |
|---|---|
| 基础 40 次主请求、逐例表、判分、诊断、变体、改进配对 | ✅ |
| 正式题参考答案 | ✅（Claude 标注、本人逐题核对；未经独立第三方标注） |
| 语义支持检查 | ⚠ 仅人工规则近似（`results/scoring/人工核查.md`），未实现模型/NLI 级检查 |
| B：主问题（换版本显示旧结论）复现、区分原因、最小修复、回归、变体、页面 | ✅ |
| B：R03 漏证据、R07 未知文档 invalid_scope | ❌ 已登记未修复（b_checks B12/B14） |
| 可选演示视频 | 未做 |
