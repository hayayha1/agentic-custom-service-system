# 文档导航

返回[项目首页](../README.md)。设计文档描述目标或历史方案，实际实现状态以代码、运行指南及测试报告为准。

## 架构与规范

| 文档 | 内容 |
|---|---|
| [系统功能设计](architecture/system_spec.md) | 知识库、检索和会话模块的原始设计 |
| [Agent 重构方案](architecture/agent_refactor_plan.md) | 规划执行、工具网关、记忆、持久化、观测和评测的目标架构 |

## 运行指南

- [目录迁移对照](guides/repository_layout.md)：旧路径、新路径及本地产物的保留位置。
- [Agent 运行与迁移](guides/agent_runtime.md)：状态库、Redis、OTLP、审批恢复、离线评测与部署边界。
- [脚本入口](../scripts/README.md)：当前支持的命令与历史脚本归档。
- [测试说明](../tests/README.md)：隔离数据库测试与已知失败。
- [监控配置](../ops/README.md)：指标端点、Grafana 模板与告警规则。

## 业务设计与历史方案

- [角色与权限](design/roles_and_permissions_scheme.md)
- [SaaS 产品与订阅](design/SAAS_PRODUCT_AND_SUBSCRIPTION_PLAN.md)
- [RAG 到 Agent 的演进方案](design/RAG_TO_AGENT_CUSTOMER_SERVICE_PLAN.md)
- [BadCase 闭环方案](design/BADCASE_CLOSED_LOOP_SOLUTION.md)
- [BadCase 优化规范](design/BADCASE_OPTIMIZATION_SPEC.md)
- [知识来源同步设计](design/knowledge_source_sync_design.md)
- [知识来源同步功能](design/knowledge_source_sync_features.md)

## 数据与评测证据

- [评测资料索引](../data/evaluation/README.md)
- [100 条路由与 Planner 盲测集](../data/evaluation/route_planner_v1/README.md)
- [真实模型测试报告](../data/evaluation/route_planner_v1/results/native_v1/REPORT.md)
- [详细失败分析](../data/evaluation/route_planner_v1/results/native_v1/FAILURE_ANALYSIS.md)

目录整理保留了业务源码及已封存评测数据的原始路径和字节内容；历史报告中的本地绝对路径仍作为原始证据保留。生成的 Word、PPT、图片与个人展示材料归档在本地 `local_artifacts/`，不属于仓库运行依赖。
