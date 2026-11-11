# Agent 监控配置

| 文件 | 用途 |
|---|---|
| [agent_dashboard.json](agent_dashboard.json) | Grafana 仪表盘模板，导入后选择 Prometheus 数据源 |
| [agent_alerts.yml](agent_alerts.yml) | Prometheus 告警规则：P95 时延、工具失败、安全拦截与步数上限 |

应用提供 `GET /api/v1/agent/metrics`，需要平台运维权限。指标按进程累计，应分别采集各应用实例再汇总。追踪可通过 `AGENT_OTLP_ENDPOINT` 发送给支持 OTLP HTTP 的 Collector。

仓库只提供应用端能力与配置模板；启动应用不会自动安装 Redis、PostgreSQL、Prometheus、Grafana 或 Collector。当前演示认证不能直接作为公网采集认证方案。

完整配置见 [Agent 运行指南](../docs/guides/agent_runtime.md)。
