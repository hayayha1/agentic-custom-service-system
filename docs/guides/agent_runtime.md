# Agent 模块重构与运行说明

## 范围与入口

依据[Agent 重构架构方案](../architecture/agent_refactor_plan.md)实施。聊天 API 与现有订单、物流、退款、确认和澄清卡片保持兼容，新增 `agent_trace_id` 与可选 `approval_id`。

入口：`app/workflow/agent_customer_service_graph.py`，公开 `agent_customer_service_graph.ainvoke(...)`。实际编排在 `agent_runtime.py`，兼容旧 `customer_service_graph` 导入路径。调用方必须传入服务端验证的 `tenant_id/customer_id/user_id/role/session_id`，不能把模型参数作为身份来源。

```mermaid
flowchart LR
  I[输入护栏] --> P[快通道 / 原生工具调用规划 DAG]
  P --> D[决策与终止仲裁]
  D --> V[参数准备与事实核对]
  V --> C[缺参 interrupt]
  C -->|用户补充| V
  V --> A[高风险审批 interrupt]
  A -->|明确确认| T[统一工具网关]
  V -->|只读 / 低风险| T
  T --> O[标准 Observation]
  O --> D
  D --> F[证据汇总与脱敏]
```

## 方案对应实现

| 方案模块 | 实现与边界 |
|---|---|
| Plan-and-Execute + ReAct | 原生 Function Calling 提交可校验 DAG；循环读取真实工具 Observation；依赖顺序、工具类型、目标完成判定受代码约束；默认最多 8 次执行，单次请求 60 秒。 |
| 工具网关 | Pydantic 强类型与额外字段拒绝；身份从请求上下文注入；工具参数没有租户/客户身份字段；校验订单归属、退款金额上限；低危写限流、只读指数退避最多重试 3 次、故障熔断。 |
| 三级记忆 | 工作态保存在 Graph State；会话事实/实体/近期轮次通过 SQL 持久化并可选 Redis 热缓存，默认 24 小时；已成功办理的显式发票信息、地址沉淀至客户画像。超过 5 轮或上下文预算后压缩，旧轮次单独归档，支持异步摘要与语义召回。 |
| Checkpointer | 实现 LangGraph `BaseCheckpointSaver` 异步接口，持久化快照、父快照和中间 writes；Redis 缓存不可变快照，SQL 保留完整历史；开发默认 SQLite，生产使用 PostgreSQL。SQL 写入成功是提交边界，Redis 故障回读 SQL。 |
| 护栏与 HITL | 注入/敏感输入拦截、参数白名单、金额校验、递归 PII 脱敏；退款/地址修改/取消订单通过原生 `interrupt()` 挂起与 `Command(resume=...)` 恢复；否定或含糊回复不授权，审批过期、旧卡片编号不匹配均拒绝。转人工前终止后续自动处理。 |
| AgentOps | 脱敏决策、计划、工具参数/结果、时延和 Token 审计轨迹；支持 OpenTelemetry OTLP 请求父 Span 与事件子 Span；Prometheus 指标接口、Grafana 模板与告警规则。只记录决策摘要与可核验事件，不采集模型私有思维链。 |
| 专属评测 | JSONL 固化 5 类场景；优先断言工具顺序、参数、步数、审批、状态与卡片；规则通过后才能进入至少两个不同模型的独立裁判。 |
| RSI | 差评、低置信度、人工升级及失败轨迹入池；规则或原生 Function Calling 归因；候选仅可调整提示词、示例、已注册工具描述；全量相同数据集与裁判配置比较、指标严格提升且每个历史 Case 不退化后进入发布待办，不修改在线配置。 |

## 本地与生产配置

```dotenv
AGENT_DATABASE_URL=sqlite+aiosqlite:///./agent_state.db
AGENT_MAX_ITERATIONS=8
AGENT_TIMEOUT_SECONDS=60
AGENT_MEMORY_TTL_SECONDS=86400
AGENT_MEMORY_WINDOW=5
AGENT_CONTEXT_TOKENS=3000
AGENT_TOOL_TIMEOUT_SECONDS=10
AGENT_TOOL_RETRIES=3
AGENT_TOOL_RATE_LIMIT=20
AGENT_CIRCUIT_THRESHOLD=5
AGENT_CIRCUIT_RESET_SECONDS=60
```

生产实例共享以下服务（不要让多个实例各自使用本地 SQLite 文件）：

```dotenv
AGENT_DATABASE_URL=postgresql+asyncpg://user:password@postgres/agent
AGENT_REDIS_URL=redis://redis:6379/1
AGENT_OTLP_ENDPOINT=http://collector:4318/v1/traces
```

启动会创建 `agent_records`、`agent_leases`、`agent_memory_vectors` 表。PostgreSQL 需要安装 pgvector 扩展及相应建表权限；受限数据库由运维预建扩展。向量维度使用 `EMBEDDING_DIM`；变更 Embedding 模型或维度后应重建记忆向量，不能混用旧模型向量。本地使用 JSON 存储向量并计算余弦，生产使用 pgvector 距离排序。

Agent 状态库与聊天事务分开，避免 SQLite 中用户消息尚未提交时阻塞 Checkpointer。PostgreSQL 可以与应用库使用同一服务，但保留独立事务。

已配置有效 LLM 凭证时，业务规划、执行决策、缺参提取均使用原生工具调用。未配置凭证时进入标记为 `offline` 的保守规则路径，用于离线开发与回归。已配置模型却出现调用/协议异常时，会停止办理并提示人工处理，不会静默改走规则路径执行写操作。

## 交易可靠性与接管

- 同一租户、客户、会话通过 SQL 租约避免多个进程并发恢复；冲突请求返回 HTTP 409。
- 所有业务写入在调用前持久化操作编号及参数指纹。相同编号重复提交返回既有结果；相同编号更换参数会被拒绝。
- 写入超时或进程在外部提交后退出，状态标记为待核实并禁止盲目重试。真实 ERP 应接受同一个幂等键并提供结果查询接口，才能进一步实现自动对账恢复。
- 当前 `business_service` 仍是项目原有的模拟 ERP。网关将模拟数据按租户/客户隔离后持久化，防止共享内存串单。接入真实 ERP 时，需要在适配器中使用认证上下文传入租户与客户，并保留网关校验及上游幂等协议。
- 服务重启后，无需把内存字典恢复进进程：原生 Checkpointer 会恢复等待节点；确认只使用冻结参数。旧 `MemoryHub`、`ActionGuardrail` 和槽位接口保留用于历史导入兼容，不参与新工作流的状态存储与授权。

## API 与监控

| 接口 | 权限 / 用途 |
|---|---|
| `POST /api/v1/chat` | 本人客户或已授权企业人员；返回 `agent_trace_id`。确认卡片可附带 `approval_id`，前端按钮已接入。 |
| `GET /api/v1/agent/traces/{trace_id}` | 企业管理员/知识主管，仅当前租户。 |
| `GET /api/v1/agent/failures` | 当前租户的脱敏失败/反馈轨迹池。 |
| `POST /api/v1/agent/candidates` | 提交 `{"trace_ids":["..."]}` 生成离线候选。 |
| `GET /api/v1/agent/candidates/{id}` | 查看当前租户候选；没有在线自动生效接口。 |
| `GET /api/v1/agent/metrics` | 平台运维权限，Prometheus 文本格式。 |

导入 `ops/agent_dashboard.json` 并配置 Prometheus 数据源，载入 `ops/agent_alerts.yml`。采集器需通过现有认证接入 `/api/v1/agent/metrics`；目前项目仍使用演示认证，正式部署需沿用项目的认证升级流程，不能把可自报角色的演示请求头直接暴露给公网。

指标按进程累计，Prometheus 应分别采集各实例并汇总；跨实例历史轨迹由 SQL 统一保存。当前聊天 API 为一次性响应，暴露的是请求完成时延与 P95，没有把它伪报为流式首 Token 时延。Token 指标来自规划/执行模型上报的 usage，离线规则路径记为 0；摘要和独立评审模型成本需在对应服务侧另外汇总。

## 回归与候选门禁

```powershell
python -m pytest tests/test_agent_customer_service.py tests/test_agent_runtime.py tests/test_agent_api.py -q
python -m scripts.evaluate_agent --output scratch/agent-baseline.json
python -m scripts.evaluate_agent --policy candidate-policy.json --baseline scratch/agent-baseline.json --output scratch/agent-candidate.json
python -m scripts.evolve_agent --tenant-id tenant_default --output-dir scratch/agent-evolution
```

默认评测使用临时独立状态库与业务/知识故障夹具，不调用线上业务。`--live` 仅启用真实规划模型，ERP 仍为隔离模拟环境；评审团可通过重复 `--judge-model` 提供至少两个不同模型。每个裁判只读取证据，不读取其他裁判结论。`--policy` 读取 `AgentPolicy` 格式，不接受 Python 或任意代码。

19 条 JSONL 用例覆盖全部八种业务工具、缺参补全、复合任务审批、工具故障、注入、订单越权及有/无政策证据等场景。它们测量执行与护栏行为，不能替代真实知识库召回效果评测或 ERP 联调。

候选与基线分数相同也会被门禁拒绝。数据集不同、裁判配置不同、缺 Case、任一硬断言失败、任一 Case 或裁判维度退化均拒绝。候选摘要必须与被评测策略摘要一致。通过门禁仅进入发布待办，线上发布仍由正常发布流程完成。

## 验证记录与部署边界

本次验证使用无模型凭证的离线环境、隔离 SQLite 状态库、模拟 HTTP 原生工具调用及故障夹具。覆盖新实例恢复、确认与取消、过期与旧卡片拒绝、租户隔离、幂等、超时、重试熔断、Redis 故障回读、记忆压缩、原生模型观测反馈及评测门禁。

真实 Redis、PostgreSQL/pgvector、OTLP Collector、Grafana 与线上模型裁判未在本地环境连接验证；部署后需要验证对应连接、数据库权限和上游业务幂等契约。这里交付的是可运行模块、适配能力和运维配置，不代表这些外部服务已经部署。

全量测试中的企业注册角色断言 `test_user_register_with_enterprise_profile` 原本期望 `end_user`，当前注册逻辑返回 `tenant_admin`。已在原始 HEAD 副本及独立数据库中复现；该注册角色行为未纳入本次 Agent 重构。
