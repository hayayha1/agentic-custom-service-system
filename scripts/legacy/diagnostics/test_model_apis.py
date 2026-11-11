import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from app.services.model_service import model_service

async def test():
    emb = await model_service.get_embedding("测试嵌入向量")
    print("Embedding length:", len(emb) if emb else "Failed")
    scores = await model_service.rerank("退换货规则", ["7天无理由退换货规则说明", "今天天气不错"])
    print("Rerank scores:", scores)
    resp = await model_service.chat_completion([{"role": "user", "content": "请回复'API正常'"}])
    print("Chat completion:", resp)

if __name__ == '__main__':
    asyncio.run(test())
