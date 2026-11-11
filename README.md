# 知枢 SaaS · 智能客服与知识治理

基于 FastAPI、LangGraph、SQLAlchemy 和 Vue 3 的企业客服演示项目，覆盖知识检索、客户会话、人工协同、业务工具及反馈治理，并提供可复现的 Agent 评测流程。

**当前状态：可本地运行的演示与研发版本。**已有 Agent 持久化、审批恢复和工具网关实现；真实模型专项盲测尚未达标，已知缺口及原始结果公开保留，不能据此宣称已完成生产验收。

[快速启动](#快速启动) · [目录结构](#目录结构) · [测试与评测](#测试与评测) · [文档导航](docs/README.md) · [失败分析](data/evaluation/route_planner_v1/results/native_v1/FAILURE_ANALYSIS.md)

## 能做什么

| 模块 | 已有能力 |
|---|---|
| 知识库 | 按租户/产品线管理知识库，导入 Markdown、TXT、FAQ，文档分块、版本及回滚 |
| 检索与问答 | BM25 与向量召回、融合及重排，展示来源片段，低置信度推荐或兜底 |
| 会话协同 | 保存会话和消息、分配人工坐席、转人工及恢复 AI 接待 |
| Agent | 快慢路由、结构化规划、工具结果反馈循环、缺参追问、审批挂起与恢复 |
| 工具网关 | 参数校验、客户归属、风险分级、写入防重、限流、读取重试与熔断 |
| 记忆与状态 | 工作状态快照、会话实体和摘要、显式客户画像；SQL 持久化及可选 Redis 缓存 |
| 反馈治理 | 差评、低置信度和失败轨迹归集，离线候选生成、回归比较及发布待办 |
| 观测 | 脱敏执行轨迹、可选 OTLP 导出、指标接口、Grafana 模板和告警规则 |

以上为代码能力范围，具体可靠性以测试结果为准。订单、物流、退款和开票目前使用项目内的模拟业务适配器。

## 快速启动

需要 **Python 3.11 或更高版本**，当前本地验证环境为 Python 3.11.9。前端静态资源由应用提供，无需 Node.js 构建。

### Windows / PowerShell

```powershell
git clone https://github.com/hayayha1/agentic-custom-service-system.git zhishu-saas
cd zhishu-saas
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\一键启动.bat
```

启动脚本优先选择项目的 `.venv`，然后是 `venv`、系统 `python`，最后兼容原有的本机解释器路径。`一键启动.bat`、`启动客服系统.bat` 均调用同一个 `start.bat`。

也可以直接运行：

```powershell
.\.venv\Scripts\python.exe run.py
```

`run.py` 会初始化应用、建表和演示数据，自动打开浏览器。默认访问：

- 网页：[http://localhost:8000/](http://localhost:8000/)
- API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

如果 8000 被占用，启动器会尝试 8001～8099，以终端显示及自动打开的地址为准。更新代码后需停止旧服务并重新启动，启动器未开启自动重载。

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
.venv/bin/python run.py
```

## 配置

完整模板见 [.env.example](.env.example)。保留占位凭证即可体验离线路径；填写有效凭证后使用对应外部模型服务。

| 配置 | 用途 / 默认行为 |
|---|---|
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `LLM_MODEL` | 原生工具调用与语言模型，使用 OpenAI 兼容 HTTP 协议 |
| `EMBEDDING_*` / `RERANK_*` | 向量和重排模型；没有有效凭证时可使用内置降级路径 |
| `DATABASE_URL` | 会话和知识库数据库，默认 `sqlite+aiosqlite:///./knowledge_base.db` |
| `AGENT_DATABASE_URL` | Agent 独立状态库，默认 `sqlite+aiosqlite:///./agent_state.db` |
| `AGENT_REDIS_URL` | 可选 Redis 热缓存；未配置时由 SQL 承担持久化 |
| `AGENT_MAX_ITERATIONS` | 默认最多 8 次 Agent 工具执行，网关内部重试另计 |
| `AGENT_TIMEOUT_SECONDS` | 默认单次请求 60 秒，不是跨多轮会话的总时限 |
| `AGENT_OTLP_ENDPOINT` | 可选 OTLP HTTP Trace Collector 地址 |

SQLite 适合本地演示；多实例部署应使用共享 PostgreSQL，向量功能需要 pgvector。应用主库切换为 PostgreSQL 时显式配置 `PG_VECTOR_ENABLED=true`。相关权限、向量维度、Redis 与追踪配置见 [Agent 运行指南](docs/guides/agent_runtime.md)。

`.env`、本地数据库、虚拟环境、`scratch/` 和 `local_artifacts/` 不上传 GitHub。应用不会自动部署外部数据库、监控平台或真实 ERP。

## 演示账号

| 角色 | 账号 | 密码 |
|---|---|---|
| 平台管理员 | `platform_admin` | `admin123` |
| 企业管理员 | `tenant_admin` | `admin123` |
| 知识主管 | `knowledge_master` | `km123` |
| 服务坐席 | `service_agent` | `agent123` |
| 终端客户 | `end_user` | `user123` |

演示认证包含预置账号、模拟令牌及角色请求头，尚不是可直接面向公网的生产认证系统。角色说明见 [角色与权限设计](docs/design/roles_and_permissions_scheme.md)。

## 目录结构

```text
.
├── app/                         # 应用代码
│   ├── api/v1/                  # 会话、知识库、租户、同步与 AgentOps 接口
│   ├── core/                    # 配置和演示身份上下文
│   ├── db/                      # 数据库连接与初始化
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # 请求及响应契约
│   ├── services/                # Agent、检索、分块、同步与业务适配器
│   ├── static/                  # Vue 页面和嵌入式组件
│   ├── workflow/                # 工作流入口与运行时
│   └── main.py                  # FastAPI 应用及生命周期
├── data/
│   ├── md/、txt/、faq/          # 演示知识资料
│   └── evaluation/              # 回归集、盲测集、结果及历史 RAG 资料
├── docs/
│   ├── architecture/            # 系统设计与 Agent 重构方案
│   ├── design/                  # 权限、同步、订阅、BadCase 等历史设计
│   ├── guides/                  # 运行与迁移说明
│   └── README.md                # 文档导航
├── scripts/                     # 保留原命令路径的现用评测入口
│   └── legacy/                  # 历史诊断、维护、源码补丁和 RAG 工具
├── tests/                       # 自动化测试
├── ops/                         # Grafana 仪表盘与告警模板
├── local_artifacts/             # 仅本地：文稿、PPT、图片及旧生成器归档
├── scratch/                     # 仅本地：测试数据库和临时运行输出
├── .env.example                 # 环境变量模板
├── .gitattributes               # 保留封存文件的字节指纹
├── pytest.ini                   # 默认只收集 tests/
├── requirements.txt
├── run.py
├── start.bat                    # Windows 统一启动器
├── 一键启动.bat                 # 兼容快捷入口
└── 启动客服系统.bat             # 兼容快捷入口
```

实际运行时生成的 `.env` 和数据库文件可能出现在根目录；它们保留原路径，避免影响现有本地数据。历史文稿与个人演示资料已移入不上传的本地产物目录，原始路径及移动前指纹保存在该目录的清单中。

## 测试与评测

### 本地自动化测试

从根目录运行 `python -m pytest`，默认仅收集 `tests/`。测试会写入数据库，推荐先按 [测试说明](tests/README.md) 设置独立测试数据库并关闭外部模型调用。

Agent 相关回归：

```powershell
python -m pytest tests/test_agent_customer_service.py tests/test_agent_runtime.py tests/test_agent_api.py tests/test_route_planner_benchmark.py -q
```

本地断言检查与真实模型评测分别报告。全量套件中已有企业注册角色断言与现有行为不一致的问题，详见测试说明；目录整理没有通过跳过用例或更改业务行为隐藏该问题。

### 隔离业务回归

```powershell
python -m scripts.evaluate_agent --output scratch/agent-evaluation.json
```

默认运行 19 个离线场景，不提交真实业务；`--live` 会启用已配置模型。该流程与下面的路由/规划专项盲测目的不同。

### 路由与 Planner 原生模型盲测

```powershell
python -m scripts.run_route_planner_blind --mode native --repeats 3 --concurrency 3 --output scratch/route-planner-new-run
python -m scripts.score_route_planner --run-dir scratch/route-planner-new-run
```

先完成预测并封存，再读取标准答案评分。被测模型只接收问题、上下文和生产工具 Schema，推理进程禁止读取标准答案与历史结果。native 模式需要有效凭证并产生模型调用用量，输出目录必须是新目录。

### 已公开的基线结果

2026-11-07 的固定基线使用 `deepseek-chat`，100 条用例各运行 3 次：

| 指标 | 基线结果 |
|---|---:|
| 全项通过 | 164/300，54.7% |
| 路由准确率 | 71.0% |
| Deep 目标完整覆盖率 | 61.1% |
| DAG 结构合法率 | 79.4% |
| 必要依赖满足率 | 47.2% |
| 独立任务关系端到端满足率 | 57.6% |
| 结构化条件满足率 | 0% |

条件分支、路由否定/复合语义以及澄清节点契约仍有缺口。独立任务指标中有28对因上游目标缺失而无法核验；能核验的38对关系均正确，不能把全部低分都解释为模型错误串行化任务。

- [数据集与盲测约定](data/evaluation/route_planner_v1/README.md)
- [完整测试报告](data/evaluation/route_planner_v1/results/native_v1/REPORT.md)
- [详细失败原因](data/evaluation/route_planner_v1/results/native_v1/FAILURE_ANALYSIS.md)
- [46 个失败 Case 的原始证据](data/evaluation/route_planner_v1/results/native_v1/FAILED_CASE_DETAILS.md)
- [100 条逐项结果 CSV](data/evaluation/route_planner_v1/results/native_v1/case_results.csv)

基线输入、答案、预测与被测源码由指纹关联，目录整理保留其原始路径和字节内容，不改写历史成绩。

## API 与运维入口

| 前缀 / 端点 | 用途 |
|---|---|
| `/api/v1/auth` | 演示登录与身份 |
| `/api/v1/chat` | 会话、消息、业务卡片与人工协同 |
| `/api/v1/kbs`、`/documents`、`/chunks` | 知识库、文档和检索片段；后两者同样位于 `/api/v1` 下 |
| `/api/v1/badcases` | 反馈与知识治理 |
| `/api/v1/tenants`、`/api/v1/sync` | 租户管理与来源同步 |
| `/api/v1/agent/traces/{trace_id}` | 当前租户的脱敏轨迹，需相应管理权限 |
| `/api/v1/agent/metrics` | 平台运维指标 |

完整接口以启动后的 `/docs` 为准。监控模板见 [ops/](ops/README.md)，更多架构、业务设计与迁移资料见 [docs/](docs/README.md)。
