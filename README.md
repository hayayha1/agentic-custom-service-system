# 智能客服系统 (AI Customer Service Knowledge Base & RAG)

基于 **Python + FastAPI + PostgreSQL (pgvector) + LangGraph + SQLAlchemy** 构建的高可用智能客服知识库与智能检索系统。

Agent 已升级为可持久化的 Plan-and-Execute / ReAct 工作流，支持统一工具网关、审批恢复、三级记忆、观测和离线评测门禁。配置、迁移与验证边界见 [Agent 重构运行说明](docs/AGENT_REFACTOR.md)。

---

## 🌟 系统核心特性

### 1. 三种角色的权限区分体系 (RBAC)
系统严格针对当前已实现的功能，区分了三种角色的菜单能见度、操作权限与行级数据边界：
- **👤 1. 普通用户 (user)**：
  - **仅限访问【ai客服对话】**。自动隐藏【知识库管理】和【知识片段管理】；
  - **行级数据隔离**：会话列表仅展示自己本人的专属会话，无法查阅其他客户会话；
  - **允许操作**：智能问答、查看改写、查看本人业务卡片（订单/物流）、查阅命中来源详情、申请“转接人工客服”；
  - **越权拦截**：无权访问或修改知识库与知识文档，违规调用直接返回 403 Forbidden。
- **🎧 2. 技术客服 (tech_agent)**：
  - **允许访问【ai客服对话】与【知识片段管理】**。自动隐藏【知识库管理】；
  - **会话协作与接管**：可查看所有进线客户会话列表，可接管会话以座席专员身份回复，并有权点击“结束人工，切回AI”；
  - **知识片段维护**：可上传/新增文档（MD/TXT）、批量导入 FAQ、查看版本历史并执行版本回滚、删除文档；
  - **越权拦截**：无权创建/删除知识库或修改检索阈值超参，违规调用直接返回 403 Forbidden。
- **🛡️ 3. 超级管理员 (admin)**：
  - **拥有全量功能与全菜单访问权限**（ai客服对话、知识库管理、知识片段管理）；
  - **专属管理权限**：创建产品知识库、微调检索与重排阈值（TopK / 0.80 / 0.50）、执行知识库级联物理删除。

### 2. 前端三大功能模块（左侧主菜单已深度接入业务）
- **🤖 1. ai客服对话（每个用户一个独立会话）**：
  - **真实会话持久化**：会话数据（`chat_sessions`）与历史消息流（`chat_messages`）全量存入数据库，刷新页面后会话状态与问答记录无缝还原。
  - **多客户支持**：左侧展示客户列表（张先生、李总监等），支持一键“+ 接新客户”添加会话。
  - **业务接口深度接入**：用户询问“查我的订单物流”、“退款进度”时，自动路由并返回**交互式业务卡片**（订单明细、顺丰实时物流时间轴、售后退款单阶段追踪）。
  - **转人工客服闭环**：点击“👩‍💼 转接人工客服”，会话状态切换为人工座席接管，由人工客服应答，并支持随时“结束人工服务，切回AI”。
  - **知识来源联动抽屉 (Source Inspector)**：点击任意命中来源，右侧滑出抽屉，实时高亮查阅该切片的原始段落、字数及元数据，并可一键跳转至知识片段管理。
- **📚 2. 知识库管理**：
  - 按业务产品线（如 `SAAS_CLOUD`）建立独立知识库与数据隔离。
  - 知识库基础操作（新建、编辑、状态启用/停用）。
  - **级联删除机制**：删除知识库时，数据库事务级联清空关联的全部文档、历史版本、切片 (Chunks) 及向量索引。
  - **独立检索超参配置**：不同知识库可独立微调 `BM25 TopK`、`向量 TopK`、`Rerank TopK`、`直接回答阈值` (默认0.80)、`相似澄清阈值` (默认0.50)。
- **🧩 3. 知识片段管理**：
  - **支持本地文件直传**：新增文档时可直接选择本地 `.md` 或 `.txt` 文件一键上传解析，自动分块入库。
  - **版本管理与一键回滚**：文档编辑后自动归档历史快照、版本号递增并重构索引；支持查看历史版本差异并一键回滚。
  - **FAQ 批量导入**：支持标准问法 + 多个相似问法 + 标准答案结构化录入。

---

## 🛠️ 技术架构

- **后端**：Python 3.10+ / FastAPI / SQLAlchemy 2.0 (AsyncIO) / Pydantic V2
- **向量数据库与持久化**：PostgreSQL 15+ 搭配 `pgvector` 扩展（本地开发/测试模式下支持通用自适应降级模式）
- **Agent 工作流编排**：LangGraph 状态图（StateGraph）
- **混合检索与重排**：
  - 倒排分词检索：`jieba` + `rank-bm25`
  - 密集向量检索：`pgvector` 余弦近邻
  - 候选集融合：加权 RRF 算法 + 文档知识优先级系数加成
  - 语义重排：Cross-Encoder Rerank
- **前端交互**：单页极简现代化架构（Tailwind CSS + Vue 3），开箱即用无需 node_modules 繁琐编译。

---

## 🚀 快速启动指南

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python run.py
```
终端启动后将自动执行数据库建表与演示数据（Demo Seed）注入：
- 🌐 **访问系统 Web 界面**：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📖 **访问交互式 API 文档 (Swagger)**：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. 执行自动化测试
```bash
$env:PYTHONPATH="."
pytest -v tests/test_customer_service.py
```

---

## 📂 项目代码目录结构

```
d:\projects\智能客服
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py             # 智能客服对话接口 (LangGraph驱动)
│   │       ├── chunks.py           # 知识切片检索与明细
│   │       ├── documents.py        # 知识文档与FAQ管理 (版本回滚/批量导入)
│   │       ├── knowledge_bases.py  # 知识库CRUD、级联删除与配置
│   │       └── __init__.py
│   ├── core/
│   │   └── config.py               # 系统配置与环境变量
│   ├── db/
│   │   └── session.py              # 异步SQLAlchemy引擎与pgvector初始化
│   ├── models/
│   │   ├── base.py                 # ORM基类与时间戳混入
│   │   ├── chunk.py                # 知识切片与向量模型 (pgvector适配)
│   │   ├── document.py             # 知识文档模型
│   │   ├── document_version.py     # 文档历史版本快照模型
│   │   ├── faq.py                  # FAQ问答结构模型
│   │   └── knowledge_base.py       # 知识库主模型
│   ├── schemas/                    # Pydantic请求与响应契约
│   ├── services/
│   │   ├── chunking/
│   │   │   └── splitter.py         # FAQ/MD/TXT三大切片器与元数据注水
│   │   ├── model_service.py        # 大模型改写、分类、Embedding与Rerank
│   │   └── retrieval/
│   │       └── engine.py           # BM25 + 向量检索、RRF融合打分与优先级加成
│   ├── static/
│   │   └── index.html              # 完整前端演示界面
│   ├── workflow/
│   │   └── customer_service_graph.py # LangGraph全流程状态图编排
│   └── main.py                     # FastAPI入口与演示数据填充
├── tests/
│   └── test_customer_service.py    # 5大核心场景端到端自动化测试
├── knowledge_base_system_spec.md   # 详细功能设计规范与架构文档
├── requirements.txt                # 依赖包列表
├── run.py                          # 一键启动脚本
└── README.md                       # 说明文档
```
