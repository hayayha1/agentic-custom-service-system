# 评测资料索引

## Agent

| 资料 | 说明 |
|---|---|
| [agent_regression.jsonl](agent_regression.jsonl) | 19 个固定业务与护栏场景，默认使用离线夹具 |
| [route_planner_v1/](route_planner_v1/README.md) | 100 条路由与 DAG 规划用例，输入与答案分离 |
| [真实模型报告](route_planner_v1/results/native_v1/REPORT.md) | 2026-11-07 基线：100 条、每条 3 次 |
| [详细失败分析](route_planner_v1/results/native_v1/FAILURE_ANALYSIS.md) | 136 次失败的互斥归因与源码证据 |
| [逐 Case 证据](route_planner_v1/results/native_v1/FAILED_CASE_DETAILS.md) | 46 个存在失败的 Case 与实际计划 |
| [逐项结果 CSV](route_planner_v1/results/native_v1/case_results.csv) | 全部 100 条用例的重复测试结果 |

v1 数据、答案、原始预测和源码指纹保持封存，目录整理不改写历史成绩。数据集中的 `private/` 表示被测推理进程不可读取的标准答案目录，不是客户隐私数据目录。

## 历史 RAG 实验

- [原始问题与标签](test_dataset.json)
- [纯问题输入](test_questions_only.json)
- [RAG 汇总报告](RAG_EVALUATION_REPORT.md)
- [检索实验报告](result/RETRIEVAL_EXPERIMENT_REPORT.md)
- [历史检索缓存](rag_cache/cache_all_retrievals.json)

早期 RAG 数据及实验文件保留原有组织，历史生成/整理工具归档在 `scripts/legacy/rag/`。这些结果不替代 Agent 路由、DAG、工具执行或线上服务的验收。
