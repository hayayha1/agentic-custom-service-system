import asyncio
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import async_session_maker
from app.models.knowledge_base import KnowledgeBase
from app.models.bad_case import BadCase

KB_1_ID = "b34fb60a-392c-4bb2-9e10-57539b37fed2"
KB_2_ID = "kb_saas_cloud_02"

SEED_CASES = [
    # 簇 1: 鲜奶生鲜退货咨询 (5条真实口语问法，用户显式差评与未命中)
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "USER_FEEDBACK",
        "user_query": "我买的鲜奶已经喝了一半，觉得味道偏淡，可以按7天无理由申请退款吗？",
        "user_feedback_comment": "机器人回答说支持退货，但实际生鲜根本退不了，害我白填了退款单！",
        "ai_raw_response": "亲，普通商品签收后7天内支持无理由退货，请保持商品完好并提交退货退款申请。",
        "recall_sources": [{"doc_name": "01_售后与退换货规则.md", "heading_path": "2. 7天无理由退换货政策", "score": 0.6861}],
        "confidence_score": 0.68,
        "chat_context": [
            {"role": "user", "content": "你好，我三天前买了一箱鲜奶，昨天拆了一瓶喝了"},
            {"role": "assistant", "content": "您好！请问有什么可以帮您？"},
            {"role": "user", "content": "我买的鲜奶已经喝了一半，觉得味道偏淡，可以按7天无理由申请退款吗？"}
        ]
    },
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "LOW_CONFIDENCE",
        "user_query": "开封喝过的牛奶能退货吗",
        "ai_raw_response": "抱歉，我不太确定您的问题，您可以尝试联系人工客服为您解答。",
        "recall_sources": [{"doc_name": "01_售后与退换货规则.md", "heading_path": "2.2 “商品完好”判定标准", "score": 0.3120}],
        "confidence_score": 0.31,
        "chat_context": [
            {"role": "user", "content": "开封喝过的牛奶能退货吗"}
        ]
    },
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "AGENT_LABEL",
        "agent_label_category": "WRONG_ANSWER",
        "agent_label_notes": "坐席接手：鲜奶属于鲜活易腐食品，开封与生鲜均不支持7天无理由退款",
        "user_query": "生鲜鲜奶保质期短的食品拆封后退款吗？",
        "ai_raw_response": "商品签收7天内只要包装完好均可申请退货。",
        "recall_sources": [{"doc_name": "01_售后与退换货规则.md", "heading_path": "2.1 适用范围与起算时间", "score": 0.42}],
        "confidence_score": 0.42,
        "chat_context": [
            {"role": "user", "content": "生鲜鲜奶保质期短的食品拆封后退款吗？"}
        ]
    },
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "USER_FEEDBACK",
        "user_query": "鲜奶喝了几瓶不喜欢这个口味可以申请退款吗",
        "user_feedback_comment": "答非所问，完全没说生鲜拆封到底能不能退！",
        "ai_raw_response": "亲，商品退货需要不影响二次销售哦。",
        "recall_sources": [{"doc_name": "01_售后与退换货规则.md", "heading_path": "2.2 “商品完好”判定标准", "score": 0.51}],
        "confidence_score": 0.51,
        "chat_context": [
            {"role": "user", "content": "鲜奶喝了几瓶不喜欢这个口味可以申请退款吗"}
        ]
    },

    # 簇 2: 空调高空作业与楼层搬运复合费用 (跨章节未召回全)
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "USER_FEEDBACK",
        "user_query": "我买了一台空调需要安装在高楼层，无电梯楼房搬运和高空作业分别怎么收费？",
        "user_feedback_comment": "只回答了安装免费，没说高空作业费和爬楼费到底是几楼收费多少钱！",
        "ai_raw_response": "大件家电我们提供送货上门服务，空调基础安装也是免费的哦。",
        "recall_sources": [{"doc_name": "05_商品三包与质保安装.md", "heading_path": "3. 大家电及家具上门安装服务规范", "score": 0.2736}],
        "confidence_score": 0.27,
        "chat_context": [
            {"role": "user", "content": "师傅明天来装空调，我住老小区没电梯在7楼"},
            {"role": "assistant", "content": "师傅会按时上门联系您的。"},
            {"role": "user", "content": "我买了一台空调需要安装在高楼层，无电梯楼房搬运和高空作业分别怎么收费？"}
        ]
    },
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "LOW_CONFIDENCE",
        "user_query": "无电梯楼房搬运空调到7楼要多少搬运费？",
        "ai_raw_response": "请查阅大家的物流服务规范，或咨询在线客服。",
        "recall_sources": [{"doc_name": "02_物流配送与发货规范.md", "heading_path": "3. 合作物流与配送服务标准", "score": 0.33}],
        "confidence_score": 0.33,
        "chat_context": [
            {"role": "user", "content": "无电梯楼房搬运空调到7楼要多少搬运费？"}
        ]
    },
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "AGENT_LABEL",
        "agent_label_category": "MISSING_KNOWLEDGE",
        "agent_label_notes": "坐席标注：知识库未整合高空作业费（4层100元/10层150元）与超高搬运费（6层免费/7层起收）的联合解答问法",
        "user_query": "空调外机高空作业费收费标准和楼层有关系吗？",
        "ai_raw_response": "外机安装如需特殊辅材会按规定收取费用。",
        "recall_sources": [{"doc_name": "05_商品三包与质保安装.md", "heading_path": "3.2 免费安装范围与收费明示", "score": 0.44}],
        "confidence_score": 0.44,
        "chat_context": [
            {"role": "user", "content": "空调外机高空作业费收费标准和楼层有关系吗？"}
        ]
    },

    # 簇 3: 延迟发货保底赔偿与缺货赔付 (标准计算题)
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "USER_FEEDBACK",
        "user_query": "买家买了一台30元的手机壳，商家超时延迟发货，按10%算是3元，实际买家能收到多少赔偿？",
        "user_feedback_comment": "算错了！按10%是3元，但平台有最低5元保底，回答里没提保底金额！",
        "ai_raw_response": "根据延迟发货标准，商家需赔付商品实付金额的10%，因此赔付3元。",
        "recall_sources": [{"doc_name": "02_物流配送与发货规范.md", "heading_path": "2.1 延迟发货判定与赔偿", "score": 0.9433}],
        "confidence_score": 0.94,
        "chat_context": [
            {"role": "user", "content": "买家买了一台30元的手机壳，商家超时延迟发货，按10%算是3元，实际买家能收到多少赔偿？"}
        ]
    },
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "LOW_CONFIDENCE",
        "user_query": "延迟发货最低赔多少钱？有保底金额吗？",
        "ai_raw_response": "延迟发货按实付金额10%予以补偿。",
        "recall_sources": [{"doc_name": "02_物流配送与发货规范.md", "heading_path": "2.1 延迟发货判定与赔偿", "score": 0.41}],
        "confidence_score": 0.41,
        "chat_context": [
            {"role": "user", "content": "延迟发货最低赔多少钱？有保底金额吗？"}
        ]
    },

    # 簇 4: 外平台购买维修纠纷 (超范围/业务不支持)
    {
        "kb_id": KB_1_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "USER_FEEDBACK",
        "user_query": "我在其他电商平台买的吸尘器坏了，能寄到你们平台来维修吗？",
        "user_feedback_comment": "没说清楚外平台的商品到底管不管！",
        "ai_raw_response": "平台提供完善的三包维修保障，全国联保服务站均可受理。",
        "recall_sources": [{"doc_name": "05_商品三包与质保安装.md", "heading_path": "1. 概述与服务准则", "score": 0.27}],
        "confidence_score": 0.27,
        "chat_context": [
            {"role": "user", "content": "我在其他电商平台买的吸尘器坏了，能寄到你们平台来维修吗？"}
        ]
    },

    # 第二个知识库 (SaaS云平台知识库 - 运营二组负责)
    {
        "kb_id": KB_2_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "USER_FEEDBACK",
        "user_query": "企业子账号权限怎么分配？管理员被锁定了怎么重置？",
        "user_feedback_comment": "找不到企业管理员解锁的操作入口",
        "ai_raw_response": "请在个人中心查找账号设置。",
        "recall_sources": [],
        "confidence_score": 0.15,
        "chat_context": [
            {"role": "user", "content": "企业子账号权限怎么分配？管理员被锁定了怎么重置？"}
        ]
    },
    {
        "kb_id": KB_2_ID,
        "product_code": "SAAS_CLOUD",
        "case_type": "LOW_CONFIDENCE",
        "user_query": "SaaS平台主管理员账号密码忘记怎么重置",
        "ai_raw_response": "您可以尝试使用手机号验证码找回密码。",
        "recall_sources": [],
        "confidence_score": 0.20,
        "chat_context": [
            {"role": "user", "content": "SaaS平台主管理员账号密码忘记怎么重置"}
        ]
    }
]

async def seed_data():
    async with async_session_maker() as db:
        # 1. 更新主知识库名称
        kb1 = await db.get(KnowledgeBase, KB_1_ID)
        if kb1:
            kb1.name = "电商标准售后与服务知识库"
            kb1.description = "涵盖退换货、物流规范、促销价保、发票规则与国家三包全业务规章"
            kb1.product_code = "SAAS_CLOUD"
        
        # 2. 确保次知识库存在
        kb2 = await db.get(KnowledgeBase, KB_2_ID)
        if not kb2:
            kb2 = KnowledgeBase(
                id=KB_2_ID,
                name="SaaS云平台与企业服务知识库",
                description="涵盖企业组织架构、权限管理、API对接与账号安全",
                product_code="SAAS_CLOUD",
                status="ACTIVE",
                doc_count=0,
                chunk_count=0,
                config={"bm25_top_k": 15, "vector_top_k": 15, "rerank_top_k": 3}
            )
            db.add(kb2)
        else:
            kb2.name = "SaaS云平台与企业服务知识库"
            
        await db.commit()

        # 3. 播种 BadCases
        for item in SEED_CASES:
            case_obj = BadCase(
                id=str(uuid.uuid4()),
                kb_id=item["kb_id"],
                product_code=item["product_code"],
                session_id="session_" + uuid.uuid4().hex[:8],
                message_id="msg_" + uuid.uuid4().hex[:8],
                case_type=item["case_type"],
                user_query=item["user_query"],
                user_feedback_comment=item.get("user_feedback_comment"),
                agent_label_category=item.get("agent_label_category"),
                agent_label_notes=item.get("agent_label_notes"),
                ai_raw_response=item["ai_raw_response"],
                recall_sources=item["recall_sources"],
                confidence_score=item["confidence_score"],
                chat_context=item["chat_context"],
                status="PENDING"
            )
            db.add(case_obj)
            
        await db.commit()
    print("Seeded KBs and BadCases successfully.")

if __name__ == '__main__':
    asyncio.run(seed_data())
