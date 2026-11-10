"""Tenant-scoped AgentOps endpoints; candidates cannot activate live changes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.core.auth import CurrentUser, get_current_user
from app.services.agent.evolution import evolution_service
from app.services.agent.observability import agent_telemetry
from app.services.agent.storage import agent_store, tenant_key


router = APIRouter(prefix="/agent", tags=["Agent 观测与离线优化"])


def tenant_operator(user: CurrentUser = Depends(get_current_user)):
    if user.role not in {"tenant_admin", "admin", "knowledge_master", "operator"}:
        raise HTTPException(status_code=403, detail="需要企业管理员或知识主管权限")
    return user


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics(user: CurrentUser = Depends(get_current_user)):
    if user.role not in {"platform_admin", "admin"}:
        raise HTTPException(status_code=403, detail="需要平台运维权限")
    return PlainTextResponse(agent_telemetry.prometheus(), media_type="text/plain; version=0.0.4")


@router.get("/traces/{trace_id}")
async def trace_detail(trace_id: str, user: CurrentUser = Depends(tenant_operator)):
    trace = await agent_store.get(tenant_key("trace", user.tenant_id, trace_id))
    if not trace:
        raise HTTPException(status_code=404, detail="执行轨迹不存在")
    return trace


@router.get("/failures")
async def failures(user: CurrentUser = Depends(tenant_operator)):
    return await evolution_service.mine(user.tenant_id)


class CandidateRequest(BaseModel):
    trace_ids: list[str] = Field(min_length=1, max_length=20)


@router.post("/candidates")
async def propose(payload: CandidateRequest, user: CurrentUser = Depends(tenant_operator)):
    try:
        return await evolution_service.propose(user.tenant_id, payload.trace_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/candidates/{candidate_id}")
async def candidate_detail(candidate_id: str, user: CurrentUser = Depends(tenant_operator)):
    candidate = await agent_store.get(tenant_key("candidate", user.tenant_id, candidate_id))
    if not candidate:
        raise HTTPException(status_code=404, detail="候选方案不存在")
    return candidate
