from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.documents import router as doc_router
from app.api.v1.chunks import router as chunk_router
from app.api.v1.chat import router as chat_router
from app.api.v1.badcases import router as badcase_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.sync import router as sync_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.agent_ops import router as agent_ops_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(kb_router)
api_router.include_router(doc_router)
api_router.include_router(chunk_router)
api_router.include_router(chat_router)
api_router.include_router(badcase_router)
api_router.include_router(analytics_router)
api_router.include_router(sync_router)
api_router.include_router(tenants_router)
api_router.include_router(agent_ops_router)
