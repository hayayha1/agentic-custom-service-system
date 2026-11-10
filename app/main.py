import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from app.core.config import settings
from app.db.session import init_db, async_session_maker
from app.api.v1 import api_router
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.faq import FAQItem
from app.services.chunking.splitter import DocumentChunker
from app.services.model_service import model_service
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def seed_demo_data():
    """预填充演示知识库与知识数据"""
    async with async_session_maker() as db:
        # 0. 确保多租户种子数据初始化
        from app.models.tenant import Tenant
        import datetime
        t_res = await db.execute(select(Tenant).where(Tenant.tenant_code == "tenant_default"))
        t_default = t_res.scalars().first()
        if not t_default:
            t1 = Tenant(
                tenant_code="tenant_default",
                name="云创智能科技有限公司",
                status="ACTIVE",
                tier="ENTERPRISE",
                contact_name="云创超管",
                contact_phone="400-888-9999",
                contact_email="admin@yunchuang.ai",
                credit_code="91110108MA01ABC888",
                official_website="https://www.yunchuang.ai",
                industry="SaaS",
                business_desc="企业级智能客服与多模态知识协作软件",
                max_product_lines=10,
                max_seats=30,
                max_km_seats=5,
                max_kbs=30,
                max_docs_per_kb=50000,
                monthly_token_quota=20000000,
                used_tokens=142600,
                monthly_query_quota=1000000,
                used_queries=3280,
                subscribed_at=datetime.datetime.now() - datetime.timedelta(days=60),
                expires_at=datetime.datetime.now() + datetime.timedelta(days=305),
                total_paid_amount=59800.0,
                last_active_at=datetime.datetime.now(),
                llm_config={
                    "provider": "DeepSeek",
                    "model_name": "deepseek-chat",
                    "api_base": "https://api.deepseek.com",
                    "api_key": "",
                    "temperature": 0.2,
                    "max_tokens": 2048
                },
                embedding_config={
                    "provider": "SiliconFlow",
                    "model_name": "BAAI/bge-large-zh-v1.5",
                    "api_base": "https://api.siliconflow.cn/v1",
                    "api_key": "",
                    "dimensions": 1024,
                    "score_threshold": 0.50
                },
                product_lines=[
                    {
                        "code": "SAAS_CLOUD",
                        "name": "智能云平台服务线",
                        "description": "面向企业级SaaS订阅与云服务",
                        "group_name": "云创云服务客服组",
                        "created_at": "2026-10-01 10:00:00"
                    }
                ],
                staff_config=[
                    {
                        "user_id": "agent_1028",
                        "username": "service_agent",
                        "role": "service_agent",
                        "display_name": "一线技术客服坐席 (工号#1028)",
                        "product_code": "SAAS_CLOUD",
                        "group_name": "云创云服务客服组",
                        "max_concurrent_sessions": 10,
                        "status": "ONLINE"
                    },
                    {
                        "user_id": "km_001",
                        "username": "knowledge_master",
                        "role": "knowledge_master",
                        "display_name": "知识库架构主管 (工号#km01)",
                        "product_code": "SAAS_CLOUD",
                        "group_name": "云创云服务客服组",
                        "status": "ONLINE"
                    }
                ],
                brand_config={
                    "brand_name": "云创企业智能客服平台",
                    "bot_name": "小创助理",
                    "bot_avatar": "🤖",
                    "welcome_message": "您好！我是云创专属智能客服助手，已接入当前企业产品知识库，很高兴为您服务！",
                    "primary_color": "#4F46E5",
                    "theme": "indigo"
                }
            )
            t2 = Tenant(
                tenant_code="tenant_retail_a",
                name="极速新零售集团",
                status="ACTIVE",
                tier="PROFESSIONAL",
                contact_name="林经理",
                contact_phone="139-1122-3344",
                contact_email="lin@speedretail.cn",
                max_product_lines=3,
                max_seats=10,
                max_km_seats=2,
                max_kbs=8,
                max_docs_per_kb=10000,
                monthly_token_quota=5000000,
                used_tokens=560000,
                monthly_query_quota=200000,
                used_queries=8920,
                subscribed_at=datetime.datetime.now() - datetime.timedelta(days=30),
                expires_at=datetime.datetime.now() + datetime.timedelta(days=335),
                total_paid_amount=9800.0,
                last_active_at=datetime.datetime.now(),
                brand_config={
                    "brand_name": "极速新零售智能客服",
                    "bot_name": "极小速",
                    "bot_avatar": "🛍️",
                    "welcome_message": "极速新零售为您守候！门店自提、生鲜冷链及会员专属售后极速为您响应！",
                    "primary_color": "#10B981",
                    "theme": "emerald"
                }
            )
            t3 = Tenant(
                tenant_code="tenant_fin_b",
                name="恒信智投科技",
                status="TRIAL",
                tier="STARTER",
                contact_name="陈总监",
                contact_phone="137-8899-0011",
                contact_email="chen@hengxinto.com",
                max_product_lines=1,
                max_seats=3,
                max_km_seats=1,
                max_kbs=2,
                max_docs_per_kb=1000,
                monthly_token_quota=1000000,
                used_tokens=85000,
                monthly_query_quota=50000,
                used_queries=1120,
                subscribed_at=datetime.datetime.now() - datetime.timedelta(days=10),
                expires_at=datetime.datetime.now() + datetime.timedelta(days=20),
                total_paid_amount=0.0,
                last_active_at=datetime.datetime.now(),
                brand_config={
                    "brand_name": "恒信智投尊享客服",
                    "bot_name": "恒小智",
                    "bot_avatar": "💼",
                    "welcome_message": "尊敬的恒信量化客户，我是您的资产与量化策略答疑助手！",
                    "primary_color": "#F59E0B",
                    "theme": "amber"
                }
            )
            db.add_all([t1, t2, t3])
            await db.commit()
        else:
            # 补全可能缺失的字段
            if not t_default.product_lines:
                t_default.product_lines = [
                    {
                        "code": "SAAS_CLOUD",
                        "name": "智能云平台服务线",
                        "description": "面向企业级SaaS订阅与云服务",
                        "group_name": "云创云服务客服组",
                        "created_at": "2026-10-01 10:00:00"
                    }
                ]
            if not t_default.staff_config:
                t_default.staff_config = [
                    {
                        "user_id": "agent_1028",
                        "username": "service_agent",
                        "role": "service_agent",
                        "display_name": "一线技术客服坐席 (工号#1028)",
                        "product_code": "SAAS_CLOUD",
                        "group_name": "云创云服务客服组",
                        "max_concurrent_sessions": 10,
                        "status": "ONLINE"
                    },
                    {
                        "user_id": "km_001",
                        "username": "knowledge_master",
                        "role": "knowledge_master",
                        "display_name": "知识库架构主管 (工号#km01)",
                        "product_code": "SAAS_CLOUD",
                        "group_name": "云创云服务客服组",
                        "status": "ONLINE"
                    }
                ]
            if not t_default.max_product_lines:
                t_default.max_product_lines = 10
            if not t_default.max_km_seats:
                t_default.max_km_seats = 5
            if not t_default.max_docs_per_kb:
                t_default.max_docs_per_kb = 50000
            if not t_default.total_paid_amount:
                t_default.total_paid_amount = 59800.0
            if not t_default.expires_at:
                t_default.expires_at = datetime.datetime.now() + datetime.timedelta(days=305)
            await db.commit()

        # 0.1 确保极速新零售集团有演示隔离知识库
        retail_kb_res = await db.execute(select(KnowledgeBase).where(KnowledgeBase.tenant_id == "tenant_retail_a"))
        if not retail_kb_res.scalars().first():
            retail_kb = KnowledgeBase(
                product_code="RETAIL_FAST",
                name="极速新零售会员与物流售后知识库",
                description="面向新零售集团全域门店自提、会员积分权益及生鲜极速退款规程。",
                status="ACTIVE",
                tenant_id="tenant_retail_a",
                doc_count=1,
                chunk_count=2,
                config={
                    "bm25_top_k": 10,
                    "vector_top_k": 10,
                    "rerank_top_k": 3,
                    "threshold_direct": 0.80,
                    "threshold_clarify": 0.50
                },
                created_by="retail_admin",
                updated_by="retail_admin"
            )
            db.add(retail_kb)
            await db.flush()

            retail_content = """# 极速新零售门店自提与生鲜售后规范

## 一、门店极速自提规则
用户在极速小程序下单选择【门店自提】后，系统在 15 分钟内完成拣货并下发 6 位提货码。用户凭提货码或小程序会员二维码至选定门店服务台扫码提货即可。

## 二、生鲜冷链售后退款保障
生鲜果蔬及冷链食品如出现破损、变质，支持收货后 24 小时内拍照在线申请【极速无忧退款】，款项将在 10 分钟内原路原额返还至支付账户。"""

            doc_r = Document(
                kb_id=retail_kb.id,
                name="极速新零售门店自提与生鲜售后保障规范.md",
                doc_type="MD",
                content=retail_content,
                file_size=len(retail_content.encode("utf-8")),
                priority=3,
                version=1,
                status="ACTIVE",
                created_by="retail_admin",
                updated_by="retail_admin"
            )
            db.add(doc_r)
            await db.flush()

            chunks = DocumentChunker.chunk_markdown(retail_content, {"id": doc_r.id, "name": doc_r.name, "priority": 3})
            for c in chunks:
                emb = await model_service.get_embedding(c.content)
                db.add(DocumentChunk(
                    kb_id=retail_kb.id,
                    doc_id=doc_r.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    embedding=emb,
                    heading_path=c.heading_path,
                    priority=3,
                    metadata_info=c.metadata
                ))

            from app.models.chat_session import ChatSession, ChatMessage
            import datetime
            retail_session = ChatSession(
                customer_id="retail_vip_001",
                customer_name="周女士 · 极速金牌会员",
                product_code="RETAIL_FAST",
                status="AI_SERVICE",
                tenant_id="tenant_retail_a",
                last_message="门店自提需要携带什么证件？",
                last_message_at=datetime.datetime.now() - datetime.timedelta(minutes=8)
            )
            db.add(retail_session)
            await db.flush()
            db.add(ChatMessage(
                session_id=retail_session.id,
                role="user",
                content="门店自提需要携带什么证件？",
                raw_query="门店自提需要携带什么证件？"
            ))
            db.add(ChatMessage(
                session_id=retail_session.id,
                role="assistant",
                content="周女士您好！在极速新零售下单后无需携带实体身份证件，凭小程序订单详情中的 6 位提货码或会员动态二维码，前往选定门店服务台扫码直接提货即可！",
                reply_type="DIRECT_ANSWER",
                confidence_score=0.92,
                raw_query="门店自提需要携带什么证件？"
            ))
            await db.commit()

        res = await db.execute(select(KnowledgeBase).where(
            KnowledgeBase.tenant_id == "tenant_default",
            KnowledgeBase.product_code == "SAAS_CLOUD"
        ).limit(1))
        existing_kb = res.scalars().first()
        if existing_kb:
            # 即使知识库已存在，也确保会话被初始化
            from app.models.chat_session import ChatSession, ChatMessage
            import datetime
            # 确保演示客服会话中包含 U10086 张先生会话（专属技术客服接入）
            u10086_res = await db.execute(select(ChatSession).where(ChatSession.customer_id == "U10086"))
            if not u10086_res.scalars().first():
                s_u10086 = ChatSession(
                    customer_id="U10086",
                    customer_name="张先生",
                    product_code="SAAS_CLOUD",
                    status="HUMAN_CONNECTED",
                    assigned_agent="agent_1028",
                    last_message="昨日反馈设备无法连接WiFi，等待固件更新",
                    last_message_at=datetime.datetime.now()
                )
                db.add(s_u10086)
                await db.flush()
                db.add(ChatMessage(
                    session_id=s_u10086.id,
                    role="user",
                    content="设备怎么还是连不上WiFi？昨天说好的固件更新出来了吗？",
                    raw_query="设备怎么还是连不上WiFi？昨天说好的固件更新出来了吗？"
                ))
                db.add(ChatMessage(
                    session_id=s_u10086.id,
                    role="assistant",
                    content="张先生您好，理解您的着急心情。WiFi连接问题我们正在加急推进固件更新排期，请稍候，我马上为您转接专属技术座席。",
                    reply_type="HUMAN_AGENT"
                ))
                db.add(ChatMessage(
                    session_id=s_u10086.id,
                    role="system",
                    content="已为您接入专属技术客服专员（工号: agent_1028）",
                    reply_type="SYSTEM"
                ))
                await db.commit()
            return

        logger.info("Initializing Seed Demo Knowledge Base and Documents...")
        
        # 1. 创建默认演示知识库
        demo_kb = KnowledgeBase(
            tenant_id="tenant_default",
            product_code="SAAS_CLOUD",
            name="智能云平台服务与售后知识库",
            description="覆盖SaaS平台账号管理、退款售后规范、计费规则与发票开具指引。",
            status="ACTIVE",
            usage_scope="BOT_AND_AGENT",
            doc_count=0,
            chunk_count=0,
            config={
                "bm25_top_k": 15,
                "vector_top_k": 15,
                "rerank_top_k": 3,
                "threshold_direct": 0.80,
                "threshold_clarify": 0.50
            },
            created_by="system",
            updated_by="system"
        )
        db.add(demo_kb)
        await db.flush()

        # 2. 导入演示 Markdown 文档
        md_content = """# 智能云平台售后退款与服务保障规范

## 一、退款申请核心条件
购买本平台 SaaS 订阅服务或云资源实例后，自订单支付之日起 7 个自然日内，若未产生超出基础配额 5% 的计算资源消耗，用户均享有无理由全额退款权益。

## 二、退款申请标准流程
1. 登录用户控制台，点击右上角【费用中心】；
2. 进入【订单管理 - 退订与退款】页面；
3. 选择需要退款的订单编号，点击【申请退订】；
4. 填写退款原因后提交，系统将在 1~3 个工作日内原路返回支付账户。

## 三、发票开具与退款冲突说明
若用户在退款前已开具增值税电子普通发票或专用发票，退款审批前需先在财务中心作废发票或由我方开具红字发票冲抵。"""

        doc_md = Document(
            kb_id=demo_kb.id,
            name="退款政策与售后服务保障指南.md",
            doc_type="MD",
            content=md_content,
            file_size=len(md_content.encode("utf-8")),
            priority=3,
            version=1,
            status="ACTIVE",
            created_by="admin",
            updated_by="admin"
        )
        db.add(doc_md)
        await db.flush()

        # 版本归档
        db.add(DocumentVersion(
            doc_id=doc_md.id,
            version=1,
            content=md_content,
            created_by="admin"
        ))

        # 切片与向量化
        md_chunks = DocumentChunker.chunk_markdown(md_content, {"id": doc_md.id, "name": doc_md.name, "priority": 3})
        for c in md_chunks:
            emb = await model_service.get_embedding(c.content)
            db.add(DocumentChunk(
                kb_id=demo_kb.id,
                doc_id=doc_md.id,
                chunk_index=c.chunk_index,
                content=c.content,
                embedding=emb,
                heading_path=c.heading_path,
                priority=3,
                metadata_info=c.metadata
            ))

        # 3. 导入演示 FAQ 文档
        faq_items_data = [
            {
                "standard_question": "怎么办理产品退款？",
                "similar_questions": ["我要退钱", "如何申请退款流程", "购买后可以退款吗", "退订服务操作步骤"],
                "answer": "购买 7 天内且未消耗核心配额的用户，请进入【控制台 > 费用中心 > 退订与退款】提交申请，款项将在 1~3 个工作日原路退回。",
                "priority": 5
            },
            {
                "standard_question": "如何重置登录密码？",
                "similar_questions": ["忘记密码怎么办", "修改登录密码", "密码找回流程"],
                "answer": "在登录页点击【忘记密码】，通过绑定的企业邮箱或手机号码接收验证码即可完成密码重置。",
                "priority": 2
            },
            {
                "standard_question": "电子发票多长时间能开具出来？",
                "similar_questions": ["开票周期是多久", "什么时候能拿到发票", "申请发票需要几天"],
                "answer": "增值税电子普通发票提交后 1 小时内自动推送到您的预留邮箱；专用发票需人工审核，预计 1~2 个工作日开具并寄出。",
                "priority": 2
            }
        ]

        faq_text = "\n\n".join([
            f"【标准问题】: {item['standard_question']}\n" +
            (f"【相似问法】: {'；'.join(item['similar_questions'])}\n" if item.get('similar_questions') else "") +
            f"【权威解答】: {item['answer']}"
            for item in faq_items_data
        ])

        doc_faq = Document(
            kb_id=demo_kb.id,
            name="核心业务高频FAQ问答集",
            doc_type="FAQ",
            content=faq_text,
            file_size=len(faq_text.encode("utf-8")),
            priority=4,
            version=1,
            status="ACTIVE",
            created_by="admin",
            updated_by="admin"
        )
        db.add(doc_faq)
        await db.flush()

        db.add(DocumentVersion(
            doc_id=doc_faq.id,
            version=1,
            content=faq_text,
            created_by="admin"
        ))

        for item in faq_items_data:
            db.add(FAQItem(
                doc_id=doc_faq.id,
                kb_id=demo_kb.id,
                standard_question=item["standard_question"],
                similar_questions=item["similar_questions"],
                answer=item["answer"],
                priority=item["priority"]
            ))

        faq_chunks = DocumentChunker.chunk_faq(faq_items_data, {"id": doc_faq.id, "name": doc_faq.name, "priority": 4})
        for c in faq_chunks:
            emb = await model_service.get_embedding(c.content)
            db.add(DocumentChunk(
                kb_id=demo_kb.id,
                doc_id=doc_faq.id,
                chunk_index=c.chunk_index,
                content=c.content,
                embedding=emb,
                heading_path=c.heading_path,
                priority=c.metadata.get("priority", 4),
                metadata_info=c.metadata
            ))

        demo_kb.doc_count = 2
        demo_kb.chunk_count = len(md_chunks) + len(faq_chunks)

        # 4. 初始化三位核心客户的真实客服会话与业务历史记录
        from app.models.chat_session import ChatSession, ChatMessage
        import datetime

        s1 = ChatSession(
            customer_id="user_001",
            customer_name="张先生 · 钻石VIP客户",
            product_code="SAAS_CLOUD",
            status="AI_SERVICE",
            last_message="怎么退款",
            last_message_at=datetime.datetime.now() - datetime.timedelta(minutes=5)
        )
        db.add(s1)
        await db.flush()

        db.add(ChatMessage(
            session_id=s1.id,
            role="user",
            content="怎么退款",
            raw_query="怎么退款"
        ))
        db.add(ChatMessage(
            session_id=s1.id,
            role="assistant",
            content="购买本平台 SaaS 订阅服务或云资源实例后，自订单支付之日起 7 个自然日内，若未产生超出基础配额 5% 的计算资源消耗，用户均享有无理由全额退款权益。请登录费用中心在【退订与退款】中申请。",
            reply_type="DIRECT_ANSWER",
            confidence_score=0.892,
            raw_query="怎么退款",
            rewritten_query="SAAS_CLOUD产品关于退款申请流程与售后退款政策条件",
            sources=[
                {
                    "doc_id": doc_md.id,
                    "doc_name": doc_md.name,
                    "heading": "售后服务 > 退款规范",
                    "chunk_id": "chunk_demo_01",
                    "snippet": "购买本平台 SaaS 订阅服务或云资源实例后，自订单支付之日起 7 个自然日内，若未产生超出基础配额 5% 的计算资源消耗，用户均享有无理由全额退款权益。",
                    "priority": 3
                }
            ],
            suggested_questions=[]
        ))

        s2 = ChatSession(
            customer_id="user_002",
            customer_name="李总监 · 算力业务部",
            product_code="SAAS_CLOUD",
            status="AI_SERVICE",
            last_message="查我的退款进度",
            last_message_at=datetime.datetime.now() - datetime.timedelta(minutes=15)
        )
        db.add(s2)
        await db.flush()

        db.add(ChatMessage(
            session_id=s2.id,
            role="user",
            content="查我的退款进度",
            raw_query="查我的退款进度"
        ))
        db.add(ChatMessage(
            session_id=s2.id,
            role="assistant",
            content="已为您调取您名下的最新售后退款单。财务团队正在进行最终复核，详情见下方退款进度卡片：",
            reply_type="TRANSACTION",
            confidence_score=1.0,
            raw_query="查我的退款进度",
            business_data={
                "business_type": "REFUND_STATUS",
                "title": "售后退款审批单详情",
                "summary": "您名下最新订单的退款审核状态如下：",
                "order": {
                    "order_id": "ORD-20261020-3320",
                    "product_name": "高并发GPU算力云主机 (A100*8)",
                    "amount": "¥24,000.00",
                    "status_desc": "退款审核中",
                    "refund_info": {
                        "refund_id": "REF-998231",
                        "refund_amount": "¥24,000.00",
                        "stage": "财务复核",
                        "eta": "预计1个工作日内原路退回银行卡"
                    }
                }
            }
        ))

        s3 = ChatSession(
            customer_id="user_003",
            customer_name="王女士 · 开发者个人账户",
            product_code="SAAS_CLOUD",
            status="AI_SERVICE",
            last_message="发票几天能出来",
            last_message_at=datetime.datetime.now() - datetime.timedelta(minutes=30)
        )
        db.add(s3)
        await db.flush()

        await db.commit()
        logger.info(f"Seed Demo completed: 1 KnowledgeBase, 2 Documents, 3 Sessions initialized.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库与样例数据
    await init_db()
    await seed_demo_data()
    from app.services.agent.storage import agent_store
    from app.services.agent.observability import agent_telemetry
    await agent_store.setup()
    agent_telemetry.configure()
    yield
    if agent_store._redis:
        await agent_store._redis.aclose()
    if agent_telemetry.tracer:
        agent_telemetry.provider.shutdown()
    await agent_store.engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API
app.include_router(api_router, prefix=settings.API_V1_STR)

# 静态资源与前端页面挂载
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "智能客服知识库系统运行中", "docs": "/docs"}

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
