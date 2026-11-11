# 自动化测试

默认 `python -m pytest` 只收集本目录。历史手工工具已迁至 `scripts/legacy/`，避免测试收集时误执行数据库或源码补丁。

## 使用隔离数据库运行

下面的 PowerShell 命令为每次检查创建独立临时数据库，并关闭外部模型调用：

```powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$testRun = [guid]::NewGuid().ToString('N')
$env:DATABASE_URL = "sqlite+aiosqlite:///./scratch/test-chat-$testRun.db"
$env:AGENT_DATABASE_URL = "sqlite+aiosqlite:///./scratch/test-agent-$testRun.db"
$env:OPENAI_API_KEY = ''
$env:EMBEDDING_API_KEY = ''
$env:RERANK_API_KEY = ''
python -m pytest tests -q
```

环境变量只影响当前终端。测试完成后打开新终端启动正式演示，或清除这些临时变量，避免应用继续使用测试数据库。

## 测试分组

| 文件 | 覆盖内容 |
|---|---|
| `test_agent_customer_service.py` | 原有 Agent 模块及聊天业务回归 |
| `test_agent_runtime.py` | 持久化、审批、缺参、幂等、重试、熔断、记忆和模型协议 |
| `test_agent_api.py` | 会话身份隔离、审计访问及确认卡片 |
| `test_route_planner_benchmark.py` | 评分器规则、图校验与答案读取拦截 |
| 其他 `test_*.py` | 知识库、权限、多租户、订阅、人工协同和来源同步 |

Agent 专项回归：

```powershell
python -m pytest tests/test_agent_customer_service.py tests/test_agent_runtime.py tests/test_agent_api.py tests/test_route_planner_benchmark.py -q
```

这组本地自动化检查与真实模型盲测分开。真实模型结果见 [100 条盲测集](../data/evaluation/route_planner_v1/README.md)，不能把本地断言通过率作为模型能力成绩。

## 已知失败

`test_saas_portal_subscription.py::test_user_register_with_enterprise_profile` 期望注册角色为 `end_user`，现有企业注册逻辑返回 `tenant_admin`。该差异已在 Agent 重构前的代码中复现；目录整理没有更改此业务行为。全量测试应如实保留该失败，不能通过跳过用例来宣称全部通过。
