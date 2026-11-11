# 脚本入口

所有命令从项目根目录运行。应用启动使用根目录的 `run.py` 或一键启动脚本，以下脚本不参与服务启动。

## 当前支持的评测命令

| 入口 | 用途 | 是否需要模型凭证 |
|---|---|---|
| `python -m scripts.evaluate_agent` | 隔离状态库中的 19 场景执行回归；`--live` 使用真实规划模型 | 默认不需要 |
| `python -m scripts.run_route_planner_blind` | 只读问题与上下文，生成路由及计划预测 | native 模式需要 |
| `python -m scripts.score_route_planner` | 原始预测封存后加载标准答案评分 | 不需要，不调用模型 |
| `python -m scripts.analyze_route_planner_failures` | 从已归档结果生成详细失败分析 | 不需要 |
| `python -m scripts.build_route_planner_dataset` | 构建并冻结 v1 数据集；已存在时拒绝覆盖 | 不需要 |
| `python -m scripts.evolve_agent` | 从失败池生成候选，隔离评测后决定是否进入发布待办 | 默认离线，真实模型需 `--live` |

`route_planner_common.py` 是输入契约和文件指纹的公共模块，不是独立命令。以上入口保留原路径，既有命令仍可使用。

```powershell
python -m scripts.evaluate_agent --output scratch/agent-evaluation.json
python -m scripts.run_route_planner_blind --mode native --repeats 3 --concurrency 3 --output scratch/route-planner-new-run
python -m scripts.score_route_planner --run-dir scratch/route-planner-new-run
```

原生盲测会调用已配置模型并产生 API 用量。输出目录必须是新目录；先完成预测并生成封存记录，再运行评分。标准答案与历史结果不会进入被测模型请求。

`analyze_route_planner_failures` 针对已发布的 `native_v1` 归档进行诊断，要求当前被测源码指纹与该基线相同。它不会调用模型；需要保留归档原貌时直接阅读已有报告即可。

## 历史脚本

早期开发工具已原样归档，并更新内部路径引用：

| 目录 | 内容 |
|---|---|
| `legacy/diagnostics/` | 手工查表、检查切片、检索排查、接口与权限验证 |
| `legacy/maintenance/` | 早期建表、样本初始化、重建索引与数据修复 |
| `legacy/patches/` | 前端生成、源码补丁与旧功能合并脚本 |
| `legacy/rag/` | 历史 RAG 实验、结果整理及问题提取 |

这些工具可能包含固定知识库 ID、直接写库或改写源码的操作，不属于推荐的一键运行流程。先检查对应脚本参数与目标数据库，再按需从根目录运行，例如 `python -m scripts.legacy.diagnostics.check_tables`。

`legacy/patches/build_frontend.py` 保留了早期前端模板/补丁材料，目录整理前已存在 Python 语法问题，不作为可直接执行的入口；应用直接使用 `app/static/` 中的页面。

历史检索缓存位于 [data/evaluation/rag_cache/](../data/evaluation/rag_cache/)，人工诊断脚本不再与 `tests/` 中的自动化用例混放。根目录 `pytest.ini` 将默认测试发现范围限定为 `tests/`。
