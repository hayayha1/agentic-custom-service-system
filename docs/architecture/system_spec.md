# 智能客服系统 - 知识库与智能检索模块详细功能设计文档

---

## 1. 系统概述与技术架构

### 1.1 系统定位
本模块作为智能客服系统的核心大脑，负责知识数据的全生命周期管理（接入、清洗、分块、向量化、版本治理）、运行时 Query 智能预处理、混合多路召回（BM25 + 向量）、重排打分及三层分流应答决策，最终为前端多租户/多客户客服会话提供高准确率、带溯源、可兜底的智能化服务。

### 1.2 核心技术栈
- **后端框架**：Python 3.10+ / FastAPI（异步高性能接口、依赖注入与 OpenAPI 规范）
- **数据持久化与向量库**：PostgreSQL 15+ 搭配 `pgvector` 扩展（统一承载关系型元数据与 Chunk 密集向量）
- **ORM 与数据库迁移**：SQLAlchemy 2.0 (AsyncIO) + Alembic
- **工作流与 Agent 编排**：LangGraph（用于编排 Query 清洗改写、意图分类、多路召回、状态机控制与决策分流）
- **检索引擎与重排**：
  - 倒排文本检索：BM25（可基于 PostgreSQL 内置 Full-Text Search / Jieba 分词或独立内存 BM25 模块）
  - 密集向量检索：HNSW / IVFFlat 向量索引（搭配主流通用/中文 Embedding 模型，如 `bge-base-zh-v1.5` / `text-embedding-3-small`）
  - 语义重排：Cross-Encoder Reranker（如 `bge-reranker-large` / Cohere Rerank）

---

## 2. 知识库管理模块

### 2.1 业务逻辑与多产品隔离
系统支持按“产品线/业务域”维度建立独立的知识库。不同产品具备独立的检索参数配置、知识隔离边界与客服绑定规则。

### 2.2 数据字典（知识库维度）

| 字段名称 | 字段类型 | 约束/默认值 | 字段说明 |
| :--- | :--- | :--- | :--- |
| `id` | UUID / BIGINT | Primary Key | 知识库唯一标识符 |
| `product_code` | VARCHAR(64) | NOT NULL, INDEX | 归属产品/业务线编码（如 `APP_MALL`, `SAAS_CORE`） |
| `name` | VARCHAR(128) | NOT NULL | 知识库名称（同产品下唯一） |
| `description` | TEXT | NULLABLE | 知识库背景与业务覆盖描述 |
| `status` | ENUM / VARCHAR(16) | `ACTIVE` / `INACTIVE` | 状态：`ACTIVE`(启用) / `INACTIVE`(停用)。停用后不参与线上检索 |
| `doc_count` | INT | DEFAULT 0 | 关联文档总数（冗余统计字段，定时或事件更新） |
| `chunk_count`| INT | DEFAULT 0 | 关联生效切片（Chunk）总数 |
| `config` | JSONB | NOT NULL | 检索配置参数快照（详见第 5 节） |
| `created_by` | VARCHAR(64) | NOT NULL | 创建人用户名/工号 |
| `updated_by` | VARCHAR(64) | NOT NULL | 最后修改人用户名/工号 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 最后更新时间 |

### 2.3 操作功能矩阵
1. **创建知识库**：
   - 必须指定产品归属，初始化默认检索阈值与 Rerank 参数模板。
2. **编辑知识库**：
   - 支持修改基本属性（名称、描述、状态），支持单独微调该知识库的检索超参。
3. **删除知识库（级联硬/软删除）**：
   - **级联删除约束**：执行物理删除前弹出二次输入确认；底层通过数据库事务联动级联删除或软删除该知识库下挂载的全部知识文档（Document）、历史版本（DocumentVersion）、分块（Chunk）及对应向量索引数据。
4. **状态切换**：
   - 停用状态下立即对线上问答检索生效（从当前活跃路由表中剔除）。

---

## 3. 知识文档与 FAQ 管理模块

### 3.1 知识文档类型定义
系统支持三大类知识来源：
1. **FAQ 类型（结构化问答）**：
   - 核心结构：1 个标准问题（Standard Query）+ N 个相似问法（Similar Queries）+ 1 个标准答案（Rich-text/Markdown Answer）。
   - 导入支持：支持 Excel/CSV 格式批量导入与在线模板下载校验。
2. **Markdown (MD) 文档**：
   - 具备清晰的标题层级（H1/H2/H3/H4）、列表与代码块，适合结构化技术与业务手册。
3. **TXT 纯文本文档**：
   - 无明显排版格式的长篇非结构化通函、合同或产品说明。

### 3.2 数据字典（知识文档维度）

| 字段名称 | 字段类型 | 约束/默认值 | 字段说明 |
| :--- | :--- | :--- | :--- |
| `id` | UUID / BIGINT | Primary Key | 文档唯一标识符 |
| `kb_id` | UUID / BIGINT | FK, NOT NULL | 归属知识库 ID（建立外键索引） |
| `name` | VARCHAR(255) | NOT NULL | 文档标题/文件名称 |
| `doc_type` | VARCHAR(16) | `FAQ`, `MD`, `TXT` | 文档格式类型 |
| `file_size` | BIGINT | DEFAULT 0 | 文件大小（字节 Byte，FAQ 为纯文本字节累计） |
| `priority` | INT | DEFAULT 1 (1~5) | 知识优先级（数值越高权重越大，用于混合融合打分） |
| `version` | INT | DEFAULT 1 | 当前发布版本号（递增整数） |
| `status` | VARCHAR(16) | `INDEXING`, `ACTIVE`, `FAILED` | 向量化索引状态 |
| `created_by` | VARCHAR(64) | NOT NULL | 创建人 |
| `updated_by` | VARCHAR(64) | NOT NULL | 更新人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 修改时间 |

### 3.3 FAQ 批量导入与数据契约
批量导入上传解析规则：
- **Excel/CSV 规范列**：
  - `标准问题`（必填，<=200字）
  - `相似问法`（选填，多个相似问之间使用中英文换行符或分号 `;` 分隔）
  - `标准答案`（必填，支持 Markdown 格式，<=2000字）
  - `优先级`（选填，1~5，缺省默认 1）
- **数据清洗规则**：剔除重复行，过滤前后空格；相似问与标准问自动去重。

### 3.4 操作与生命周期管理
- **组合条件分页查询**：支持按 `name`（模糊匹配）、`doc_type`（精确筛选）、`priority`（区间或离散筛选）、`status`、`kb_id` 联合查询。
- **文档查看与在线编辑**：
  - 编辑内容后，系统自动提升 `version`，并将旧版本快照沉淀入 `document_versions` 表。
  - 编辑保存后异步触发重新解析、切片与向量化更新管道。
- **版本回滚（Rollback）**：
  - 用户可查看指定文档的历史版本日志（包含修改人、修改时间、变更 Diff）。
  - 点击“回滚至此版本”后，将该版本内容置为当前内容，version 自动 +1，并重构切片索引。
- **文档删除**：删除文档时，同步清除其所有关联的 Chunk 和向量 Embedding。

---

## 4. 文档自动切片与元数据治理（Chunking Engine）

不同类型文档采用异构的分块策略，以保证进入向量库与 BM25 的语料具有最佳的语义局部性。

```
                ┌───────────────┐
                │  知识文档入库  │
                └───────┬───────┘
                        │ 类型路由
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    【FAQ 类型】    【Markdown 类型】 【TXT 纯文本类型】
   不执行机械切片     基于 Header 层级   递归字符切片器
   1条FAQ = 1 Chunk   语义分块 (200~600) (chunk_size=500, overlap=50)
         │              │              │
         └──────────────┼──────────────┘
                        ▼
             【Chunk 元数据深度注水】
      (kb_id, doc_id, doc_type, priority,
       chunk_index, heading_path, parent_title)
                        ▼
             【双路索引同步生成写入】
           BM25 文本分词 + pgvector 密集向量
```

### 4.1 分块规则设计
1. **FAQ 类型（语义原子化，零切片）**：
   - **规则**：一条 FAQ 记录作为一个不可分割的独立 Chunk。
   - **检索特征增强**：在做向量 Embedding 时，对语料进行拼装加权：  
     `Vector_Content = f"问题: {standard_query}\n相似表达: {similar_queries}\n答案: {answer}"`
2. **Markdown 类型（语义层次切片）**：
   - **规则**：采用 `MarkdownHeaderTextSplitter`，按照 `#`、`##`、`###` 逻辑段落进行拆解。
   - **分块阈值**：Chunk 大小控制在 300 ~ 600 Token；若某个三级标题下内容超出 800 Token，则结合递归切片次级分割。
   - **上下文继承**：保留各级标题层级路径（Breadcrumb，如 `产品手册 > 售后政策 > 退款流程`）。
3. **TXT 纯文本类型（递归字符切片）**：
   - **规则**：采用 `RecursiveCharacterTextSplitter`。
   - **分割符优先级**：`["\n\n", "\n", "。", "！", "？", "；", " ", ""]`。
   - **参数配置**：`chunk_size = 500` 字符，`chunk_overlap = 50` 字符（保持边界上下文连续）。

### 4.2 Chunk 元数据（Metadata）规范
每个生成的 Chunk 均须附带丰富的不可变元数据，用于后续的精确过滤与溯源定位：

```json
{
  "chunk_id": "c-9f8a32b1-3e44-4b55-a0c1",
  "kb_id": "kb-1002",
  "product_code": "SAAS_PRO",
  "doc_id": "doc-8841",
  "doc_name": "SaaS平台全模块退款与服务变更指南.md",
  "doc_type": "MD",
  "priority": 3,
  "version": 2,
  "chunk_index": 4,
  "heading_path": "售后服务 > 退款规范 > 争议仲裁",
  "char_count": 420,
  "created_at": "2026-10-26T10:30:00Z"
}
```

---

## 5. 知识库检索配置中心

每个知识库支持独立配置检索策略，以兼顾不同产品的精度要求（例如：金融核心产品对精准度要求极高，通用电商产品更倾向扩大召回）：

| 配置项 | 参数 Key | 默认推荐值 | 可调区间 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **BM25 召回条数** | `bm25_top_k` | 15 | 5 ~ 50 | 倒排关键词初筛候选数 |
| **向量检索召回数** | `vector_top_k`| 15 | 5 ~ 50 | 密集向量近邻初筛候选数 |
| **混合权重比例** | `hybrid_weights` | `[0.4, 0.6]` | 0.0 ~ 1.0 | `[BM25权重, 向量权重]` 或 RRF 参数 `k=60` |
| **Rerank 模型类型**| `rerank_model` | `bge-reranker` | - | 指定 Cross-Encoder 算力通道 |
| **Rerank 最终保留数**| `rerank_top_k` | 3 | 1 ~ 10 | 最终输入 Prompt 生成阶段的上下文 Chunk 数 |
| **直接回答置信阈值**| `threshold_direct`| 0.80 | 0.70 ~ 0.95 | 得分高于此阈值直接触发大模型生成回答 |
| **相似澄清置信阈值**| `threshold_clarify`| 0.50 | 0.30 ~ 0.70 | 得分在 `[0.50, 0.80)` 之间触发相似问题推荐 |
| **兜底分流阈值** | `threshold_fallback`| 0.50 | - | 得分低于此阈值直接进入兜底话术 |

---

## 6. Query 预处理链路（基于 LangGraph）

用户口语化、倒装、错别字及指代不清严重影响检索质量。在正式发起向量与 BM25 检索前，必须执行流水线级 Query 预处理。

```
                ┌────────────────┐
                │ 客户端用户问句  │
                └───────┬────────┘
                        ▼
              ┌────────────────────┐
              │ 节点 1: Query 清洗 │
              └─────────┬──────────┘
                        │
                【敏感词风控拦截】
               /                 \
        [命中敏感词]          [合规正常]
             │                     │
             ▼                     ▼
    ┌─────────────────┐  ┌──────────────────────┐
    │ 触发安全拒答    │  │ 节点 2: 意图分类识别 │
    │ 阻断全链路并结束│  └──────────┬───────────┘
    └─────────────────┘             │
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
              【业务接口查询类】            【事实类知识问答】
            （查订单、看物流、改密码）      （咨询政策、原理、标准FAQ）
                      │                           │
                      ▼                           ▼
              走外部 API / Tool Calling     ┌──────────────────────┐
                                            │ 节点 3: LLM 轻量改写 │
                                            └──────────┬───────────┘
                                                       │
                                                       ▼
                                            【输出双路检索 Query】
                                            - 原始 Query: $Q_{raw}$
                                            - 改写 Query: $Q_{rewritten}$
```

### 6.1 预处理阶段详细说明

#### 步骤 1：文本清洗与敏感词拦截（P0）
- **无意义符号清洗**：剔除 Emoji、多余无意义标点、HTML/脚本标签、多余空格。
- **敏感词与注入拦截**：
  - 基于 DFA（确定有穷自动机）或 AC 自动机算法构建高敏感词/Prompt 注入词表。
  - **决策**：若命中敏感词，直接阻断后续检索与 LLM 调用，立即返回预设的安全兜底话术（如：“抱歉，该提问包含敏感或不合规内容，暂无法为您提供解答。”），并记录风控审计日志。

#### 步骤 2：意图分类标记（Classifier）
- **分类标准**：
  - `INTENT_KNOWLEDGE`（事实知识类）：咨询业务政策、办理条件、产品功能等。走知识库检索。
  - `INTENT_TRANSACTION`（事务/业务接口类）：如“帮我查一下我的尾号 4321 订单到哪了”、“我要修改收货地址”。分流至外部业务 Tool 调用，避免无意义的知识库检索开销。
  - `INTENT_CHITCHAT`（通用闲聊）：走轻量打招呼或直接转人工引导。

#### 步骤 3：LLM 轻量改写（Query Rewrite）
- **改写目标**：补全上下文指代、补充主语、将口语化表述映射到专业产品词汇。
- **Prompt 策略（小参数/低延迟模型执行）**：
  - *输入*：用户：“怎么退款”
  - *系统上下文*：当前产品 = “智能云SaaS”
  - *输出改写结果*：“智能云SaaS产品退款申请条件与退款操作流程”
- **双路下发机制**：
  输出 `$Q_{raw}$`（原始清洗词）和 `$Q_{rewritten}$`（标准化规范词），合并注入下游的检索管道。

---

## 7. 混合检索、融合重排与决策流

### 7.1 检索架构设计

```
        $Q_{raw}$ (原始问句)            $Q_{rewritten}$ (标准化改写问句)
            │                                  │
    ┌───────┴───────┐                  ┌───────┴───────┐
    ▼               ▼                  ▼               ▼
【BM25检索】   【向量检索】          【BM25检索】   【向量检索】
 (倒排关键词)  (pgvector密集向量)    (倒排关键词)  (pgvector密集向量)
    │               │                  │               │
    └───────┬───────┘                  └───────┬───────┘
            │ 候选集去重与初筛                 │
            └─────────────────┬────────────────┘
                              ▼
                   【候选集混合融合打分】
                - RRF (倒数排名融合) 或加权求和
                - 乘以文档/Chunk 知识优先级系数
                              ▼
                   【Top-N 进入 Cross-Encoder Rerank】
                              ▼
                     【得到全局最佳得分 S】
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       S >= 0.80        0.50 <= S < 0.80     S < 0.50
     【高置信度】         【中置信度】       【低置信度】
     LLM 生成回答         推荐相似相关问题    标准兜底安抚
     附带溯源来源引用     支持点击直接发起提问  引导重新表达
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                 【全链路均提供“一键转人工”入口】
```

### 7.2 检索与融合核心步骤
1. **多路并行召回**：
   - 使用 `$Q_{raw}$` 和 `$Q_{rewritten}$` 分别在 PostgreSQL 中执行 BM25 检索和向量近似近邻检索（`<=>` 余弦距离）。
   - 过滤条件强制带上：`kb_id = :target_kb_id AND status = 'ACTIVE'`。
2. **候选集混合融合打分（Hybrid Fusion + Priority Weighting）**：
   - 采用加权 RRF（Reciprocal Rank Fusion）算法将四组初筛列表合并为一个去重列表：
     $$RRF\_Score(d) = \sum_{m \in M} \frac{w_m}{k + rank_m(d)}$$
   - **知识优先级融合**：
     $$Score_{final\_candidate}(d) = RRF\_Score(d) \times (1.0 + (Priority_d - 1) \times 0.15)$$
     *（文档优先级越高，在同等相似度下获得的排位加成越明显，避免通用低效文档压过官方核心文档）*。
3. **Cross-Encoder Reranker 重排**：
   - 将 Top-15 候选 Chunk 与 `$Q_{rewritten}$` 送入重排模型，得到绝对置信度分数 $S \in [0.0, 1.0]$。
   - 截取最终 Top-K（如前 3 条）作为核心证据上下文。

---

## 8. 三层置信度决策矩阵与应答策略

系统根据最终 Rerank 排名第一的置信度得分 $S$，实施严格的三层动态应答策略：

### 8.1 决策分流矩阵

| 分值区间 | 置信度评级 | 响应逻辑与行为 | 来源溯源要求 | 转人工选项 |
| :--- | :--- | :--- | :--- | :--- |
| **$S \ge 0.80$** | **高置信度 (High)** | **直接回答**：基于召回的高相关 Chunk 组装 Prompt，调用大模型生成答案，语气专业客观。 | **必须附带**：展示来源知识库、文档标题及对应章节（如 `[来源: SaaS平台退款指南 > 第2章]`）。 | 附在卡片底部操作栏 |
| **$0.50 \le S < 0.80$**| **中置信度 (Medium)**| **澄清引导**：系统判定用户意图存在歧义或知识覆盖不完全。不强行猜测，给出 2~3 个相关相似问题卡片，支持用户点击发起精准检索。 | 仅在各相似问题候选项右下角展示精简来源。 | 明显常驻提示：“以上均不符合？[联系人工客服]” |
| **$S < 0.50$** | **低置信度 (Low)** | **兜底回复**：“抱歉，暂时没有检索到与您问题完全匹配的内容。您可以尝试换一种说法，或者直接联系我们的人工客服处理。” | 无 | 主按钮高亮突显：“立即转接人工” |

### 8.2 高置信度下的“回答带来源”（Source Attribution）格式
LLM 最终返回给前端的响应体示例：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reply_type": "DIRECT_ANSWER",
    "confidence_score": 0.885,
    "content": "根据平台退款管理规定，购买产品 7 天内且未产生核心数据消耗的用户，可在【控制台-财务中心-发票与退款】中直接申请全额退款。审批流程通常在 1~3 个工作日内完成。",
    "sources": [
      {
        "doc_id": "doc-8841",
        "doc_name": "SaaS平台全模块退款与服务变更指南.md",
        "heading": "售后服务 > 退款规范",
        "chunk_id": "c-9f8a32b1-3e44-4b55-a0c1"
      }
    ],
    "action_buttons": [
      { "action": "TRANSFER_TO_HUMAN", "label": "转接人工客服" }
    ]
  }
}
```

### 8.3 中置信度下的“相似问题推荐”响应体示例
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reply_type": "RECOMMEND_QUESTIONS",
    "confidence_score": 0.672,
    "content": "您是不是想咨询以下问题？您可以直接点击查看答案：",
    "suggested_questions": [
      { "question_id": "faq-101", "title": "不同计费模式下的退款规则说明" },
      { "question_id": "faq-102", "title": "退款退回到银行卡需要多长时间？" },
      { "question_id": "faq-103", "title": "发票已开具情况下的退款要求" }
    ],
    "action_buttons": [
      { "action": "TRANSFER_TO_HUMAN", "label": "以上都不是，转人工客服" }
    ]
  }
}
```

---

## 9. 多客户客服聊天交互界面规范

1. **多会话/多客户隔离**：
   - 界面左侧展示客户会话列表（支持接入不同端、不同客户 ID、会话状态标签）。
   - 顶部标明客户归属产品，自动对应路由到该产品的专属知识库。
2. **富文本与结构化卡片渲染**：
   - Markdown 实时流式打字机（SSE 协议）。
   - 引用角标悬停：正文中出现的 `[1]`、`[2]` 支持鼠标悬浮浮窗预览原文章节片段。
   - 底部来源折叠面板：明确罗列引用的文档名称与命中段落。
3. **交互操作区**：
   - 推荐相似问题以标签气泡（Pill Tags）呈现，点击立即发送。
   - 底部常驻“转人工客服”快捷按钮，并支持状态机平滑切换（进入人工排队 -> 人工接入中 -> 结束人工返回机器人）。

---

## 10. 物理数据库表结构设计（PostgreSQL + SQLAlchemy 2.0）

```sql
-- 1. 开启 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 知识库主表
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    doc_count INT NOT NULL DEFAULT 0,
    chunk_count INT NOT NULL DEFAULT 0,
    config JSONB NOT NULL DEFAULT '{
        "bm25_top_k": 15,
        "vector_top_k": 15,
        "rerank_top_k": 3,
        "threshold_direct": 0.80,
        "threshold_clarify": 0.50
    }'::jsonb,
    created_by VARCHAR(64) NOT NULL,
    updated_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_kb_product_code ON knowledge_bases(product_code);

-- 3. 知识文档主表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    doc_type VARCHAR(16) NOT NULL, -- 'FAQ', 'MD', 'TXT'
    file_size BIGINT NOT NULL DEFAULT 0,
    priority INT NOT NULL DEFAULT 1,
    version INT NOT NULL DEFAULT 1,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    created_by VARCHAR(64) NOT NULL,
    updated_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_doc_kb_id ON documents(kb_id);
CREATE INDEX idx_doc_query_filter ON documents(kb_id, doc_type, priority);

-- 4. 文档历史版本表 (用于版本回滚)
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version INT NOT NULL,
    content TEXT NOT NULL,
    metadata_snapshot JSONB,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_doc_ver_lookup ON document_versions(doc_id, version);

-- 5. 知识分块与向量表 (Chunks)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024), -- 适配 1024 维 Embedding 模型
    heading_path VARCHAR(512),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chunk_kb_doc ON document_chunks(kb_id, doc_id);
-- 创建 HNSW 向量索引 (余弦距离)
CREATE INDEX idx_chunk_embedding ON document_chunks 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 6. FAQ 专属扩展表 (存储标准问与相似问列表)
CREATE TABLE faq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    standard_question TEXT NOT NULL,
    similar_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    answer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_faq_kb_id ON faq_items(kb_id);
```

---

## 11. LangGraph 状态图定义伪代码

```python
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    kb_id: str
    product_code: str
    raw_query: str
    cleaned_query: str
    rewritten_query: str
    is_sensitive: bool
    intent_category: str  # "KNOWLEDGE" | "TRANSACTION" | "CHITCHAT"
    candidates: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    top_score: float
    decision_type: str    # "DIRECT" | "CLARIFY" | "FALLBACK" | "BLOCK"
    final_output: Dict[str, Any]

# 构建图流程
workflow = StateGraph(AgentState)

# 注册节点
workflow.add_node("clean_and_filter", clean_and_sensitive_filter_node)
workflow.add_node("intent_classifier", classify_intent_node)
workflow.add_node("query_rewrite", query_rewrite_node)
workflow.add_node("hybrid_retrieve", hybrid_retrieval_node)
workflow.add_node("rerank_scoring", rerank_and_score_node)
workflow.add_node("direct_answer", generate_direct_answer_node)
workflow.add_node("suggest_clarify", generate_clarify_questions_node)
workflow.add_node("fallback_reply", generate_fallback_node)
workflow.add_node("block_reply", generate_blocked_response_node)

# 边与条件路由
workflow.set_entry_point("clean_and_filter")

def check_sensitive(state: AgentState):
    return "blocked" if state["is_sensitive"] else "normal"

workflow.add_conditional_edges(
    "clean_and_filter",
    check_sensitive,
    {"blocked": "block_reply", "normal": "intent_classifier"}
)

def route_intent(state: AgentState):
    if state["intent_category"] == "KNOWLEDGE":
        return "rewrite"
    return "fallback"

workflow.add_conditional_edges(
    "intent_classifier",
    route_intent,
    {"rewrite": "query_rewrite", "fallback": "fallback_reply"}
)

workflow.add_edge("query_rewrite", "hybrid_retrieve")
workflow.add_edge("hybrid_retrieve", "rerank_scoring")

def route_decision(state: AgentState):
    score = state["top_score"]
    if score >= 0.80:
        return "direct"
    elif score >= 0.50:
        return "clarify"
    return "fallback"

workflow.add_conditional_edges(
    "rerank_scoring",
    route_decision,
    {
        "direct": "direct_answer",
        "clarify": "suggest_clarify",
        "fallback": "fallback_reply"
    }
)

workflow.add_edge("direct_answer", END)
workflow.add_edge("suggest_clarify", END)
workflow.add_edge("fallback_reply", END)
workflow.add_edge("block_reply", END)

app = workflow.compile()
```

---

## 12. 总结与后续演进建议

1. **可观测性与 Bad Case 闭环**：
   - 增加对话满意度打点（点赞/点踩），对踩的 Case 及落入中置信度（0.50~0.80）的问题自动收集进入“未命中问题库”，供知识运营人员针对性补充 FAQ 或调整优先级。
2. **性能优化保障**：
   - 在 FastAPI 中对热点问题与标准 FAQ 检索建立 Redis 缓存层；
   - 向量检索采用 HNSW 索引预加载，维持整个 P95 检索重排时延在 300ms 以内。
