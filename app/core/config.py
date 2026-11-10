import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    PROJECT_NAME: str = "智能客服知识库与智能检索系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 数据库配置（默认支持 PostgreSQL + asyncpg，支持本地 fallback）
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./knowledge_base.db"
        )
    )
    PG_VECTOR_ENABLED: bool = Field(
        default_factory=lambda: "postgresql" in os.getenv("DATABASE_URL", "sqlite")
    )

    # 默认检索参数配置
    DEFAULT_BM25_TOP_K: int = 15
    DEFAULT_VECTOR_TOP_K: int = 15
    DEFAULT_RERANK_TOP_K: int = 3
    DEFAULT_THRESHOLD_DIRECT: float = 0.80
    DEFAULT_THRESHOLD_CLARIFY: float = 0.50

    # 模型服务配置 (支持兼容 OpenAI 规范的任何大模型与 Embedding/Rerank API)
    # 默认 LLM 大模型配置（如 DeepSeek 官方）
    OPENAI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    OPENAI_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"))
    LLM_MODEL: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "deepseek-chat"))

    # 向量嵌入配置（可使用硅基流动 SiliconFlow 顶级中文 Embedding）
    EMBEDDING_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("EMBEDDING_API_KEY", ""))
    EMBEDDING_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1"))
    EMBEDDING_MODEL: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5"))
    EMBEDDING_DIM: int = 1024

    # 语义重排配置（支持硅基流动 BAAI/bge-reranker-v2-m3）
    RERANK_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("RERANK_API_KEY", ""))
    RERANK_BASE_URL: Optional[str] = Field(default_factory=lambda: os.getenv("RERANK_BASE_URL", "https://api.siliconflow.cn/v1"))
    RERANK_MODEL: str = Field(default_factory=lambda: os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3"))

    # Agent 状态库独立于聊天事务，避免 SQLite 长事务阻塞快照写入。
    AGENT_DATABASE_URL: str = "sqlite+aiosqlite:///./agent_state.db"
    AGENT_REDIS_URL: Optional[str] = None
    AGENT_MAX_ITERATIONS: int = Field(default=8, ge=1, le=32)
    AGENT_TIMEOUT_SECONDS: float = Field(default=60.0, gt=0, le=300)
    AGENT_MEMORY_TTL_SECONDS: int = 86400
    AGENT_MEMORY_WINDOW: int = 5
    AGENT_CONTEXT_TOKENS: int = 3000
    AGENT_TOOL_TIMEOUT_SECONDS: float = 10.0
    AGENT_TOOL_RETRIES: int = Field(default=3, ge=0, le=3)
    AGENT_TOOL_RATE_LIMIT: int = 20
    AGENT_CIRCUIT_THRESHOLD: int = 5
    AGENT_CIRCUIT_RESET_SECONDS: int = 60
    AGENT_OTLP_ENDPOINT: Optional[str] = None

    # 敏感词词库列表（基础默认词，支持扩展）
    SENSITIVE_WORDS: List[str] = [
        "退款漏洞", "刷单套现", "攻击系统", "黑客渗透", "洗钱",
        "色情", "暴力反动", "炸弹制作", "毒品交易", "盗刷银行卡"
    ]

settings = Settings()
