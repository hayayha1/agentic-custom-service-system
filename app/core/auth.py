from typing import List, Optional, Set, Dict, Any
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

# ===== 两级五角色体系 (已删除质检主管角色) =====

# 1. SaaS 平台层
ROLE_PLATFORM_ADMIN = "platform_admin"  # 👑 平台超级管理员 (租户生命周期、商业化履约、全平台配额治理)

# 2. 企业租户层
ROLE_TENANT_ADMIN = "tenant_admin"      # 🏢 企业租户管理员 (自主模型配置、产品线与多知识库、人员与业务分组)
ROLE_KNOWLEDGE_MASTER = "knowledge_master"  # 🧠 知识库架构主管 (知识采审终审、检索阈值调优、BadCase闭环)
ROLE_SERVICE_AGENT = "service_agent"    # 👩‍💼 一线技术客服坐席 (在线排错接单、客户协同、提报知识草稿)
ROLE_END_USER = "end_user"              # 👤 终端消费者 / 用户 (智能问答、服务评价点赞点踩、申请转人工)

# ===== 历史兼容别名 =====
ROLE_ADMIN = "admin"                    # 兼容原超级管理员
ROLE_OPERATOR = "operator"              # 兼容原知识运营专员
ROLE_TECH_AGENT = "tech_agent"          # 兼容原技术客服
ROLE_USER = "user"                      # 兼容原客户

# 全量有效角色集合（严格排除已删除的质检主管角色）
ALL_ROLES = [
    ROLE_PLATFORM_ADMIN,
    ROLE_TENANT_ADMIN,
    ROLE_KNOWLEDGE_MASTER,
    ROLE_SERVICE_AGENT,
    ROLE_END_USER,
    ROLE_ADMIN,
    ROLE_OPERATOR,
    ROLE_TECH_AGENT,
    ROLE_USER
]

# 角色等价与兼容映射字典
ROLE_ALIASES: Dict[str, Set[str]] = {
    ROLE_PLATFORM_ADMIN: {ROLE_PLATFORM_ADMIN, ROLE_ADMIN},  # 平台超管权限，老系统admin亦可访问
    ROLE_TENANT_ADMIN: {ROLE_TENANT_ADMIN, ROLE_ADMIN},      # 企业超管权限，老系统admin亦可访问
    ROLE_KNOWLEDGE_MASTER: {ROLE_KNOWLEDGE_MASTER, ROLE_OPERATOR, ROLE_ADMIN},
    ROLE_SERVICE_AGENT: {ROLE_SERVICE_AGENT, ROLE_TECH_AGENT},
    ROLE_END_USER: {ROLE_END_USER, ROLE_USER},
    # 历史角色别名向新体系投影
    ROLE_ADMIN: {ROLE_ADMIN, ROLE_TENANT_ADMIN},
    ROLE_OPERATOR: {ROLE_OPERATOR, ROLE_KNOWLEDGE_MASTER},
    ROLE_TECH_AGENT: {ROLE_TECH_AGENT, ROLE_SERVICE_AGENT},
    ROLE_USER: {ROLE_USER, ROLE_END_USER},
}

# 客服工号与负责产品线绑定字典（用于数据权限隔离与工单自动路由）
AGENT_PRODUCT_MAP = {
    "agent_1028": "SAAS_CLOUD",
    "tech": "SAAS_CLOUD",
    "agent_1029": "E_COMMERCE",
    "tech_ec": "E_COMMERCE",
    "tech_ecommerce": "E_COMMERCE",
    "agent_1030": "FIN_AI",
    "service_agent": "SAAS_CLOUD"
}

# 知识架构与运营账号与归属知识库绑定字典
OPERATOR_KB_MAP = {
    "ops": "b34fb60a-392c-4bb2-9e10-57539b37fed2",
    "ops_001": "b34fb60a-392c-4bb2-9e10-57539b37fed2",
    "km_001": None,  # 允许管理产品线下的全部知识库
    "operator": "b34fb60a-392c-4bb2-9e10-57539b37fed2",
    "ops_ecommerce": "b34fb60a-392c-4bb2-9e10-57539b37fed2",
    "ops_saas": "kb_saas_cloud_02",
    "ops_002": "kb_saas_cloud_02"
}

OPERATOR_PRODUCT_MAP = {
    "ops": "E_COMMERCE",
    "ops_001": "E_COMMERCE",
    "km_001": "SAAS_CLOUD",
    "operator": "E_COMMERCE",
    "ops_ecommerce": "E_COMMERCE",
    "ops_saas": "SAAS_CLOUD",
    "ops_002": "SAAS_CLOUD"
}

# 用户与租户归属全局映射表（动态注册与订阅开通时自动关联）
USER_TENANT_MAP: Dict[str, str] = {}

class CurrentUser(BaseModel):
    user_id: str
    username: str
    role: str
    tenant_id: str = "tenant_default"
    is_platform_admin: bool = False
    product_code: Optional[str] = None
    assigned_kb_id: Optional[str] = None
    enterprise_profile: Optional[Dict[str, Any]] = None

    @property
    def is_tenant_admin(self) -> bool:
        return self.role in [ROLE_TENANT_ADMIN, ROLE_ADMIN]

    @property
    def is_knowledge_master(self) -> bool:
        return self.role in [ROLE_KNOWLEDGE_MASTER, ROLE_OPERATOR]

    @property
    def is_service_agent(self) -> bool:
        return self.role in [ROLE_SERVICE_AGENT, ROLE_TECH_AGENT]

    @property
    def is_end_user(self) -> bool:
        return self.role in [ROLE_END_USER, ROLE_USER]

async def get_current_user(
    authorization: Optional[str] = Header(default=None, description="JWT授权令牌"),
    x_user_role: Optional[str] = Header(default=None, description="当前用户角色"),
    x_role: Optional[str] = Header(default=None, description="角色别名请求头"),
    x_user_id: Optional[str] = Header(default=None, description="当前用户ID"),
    x_user_product: Optional[str] = Header(default=None, description="所属产品线编码"),
    x_user_kb_id: Optional[str] = Header(default=None, description="归属知识库ID"),
    x_tenant_id: Optional[str] = Header(default=None, description="归属企业租户ID")
) -> CurrentUser:
    """从请求头提取当前用户上下文，支持 Header 与 Authorization Token 解析"""
    raw_role = x_user_role or x_role
    token_user_id = None
    if authorization and "Bearer " in authorization:
        token_str = authorization.replace("Bearer ", "").strip()
        for candidate_role in ALL_ROLES:
            if token_str.endswith(f"_{candidate_role}"):
                if not raw_role:
                    raw_role = candidate_role
                # 提取 token 中编码的 user_id
                for pfx in ["mock_jwt_token_for_", "token_"]:
                    if token_str.startswith(pfx):
                        token_user_id = token_str[len(pfx):-len(f"_{candidate_role}")]
                        break
                break

    role = raw_role.strip().lower() if raw_role else ROLE_USER
    if role not in ALL_ROLES:
        role = ROLE_USER
    if token_user_id:
        # Older demo tokens encoded the login alias (end_user/service_agent)
        # rather than the stable customer/agent ID returned by login.
        from app.api.v1.auth import PRESET_USERS
        preset = PRESET_USERS.get(token_user_id)
        if preset and preset["role"] == role:
            token_user_id = preset["user_id"]
    
    tenant_id = (x_tenant_id or "").strip()
    if not tenant_id:
        if token_user_id and token_user_id in USER_TENANT_MAP:
            tenant_id = USER_TENANT_MAP[token_user_id]
        elif token_user_id and token_user_id.startswith("admin_") and token_user_id not in ("admin_platform", "admin_tenant"):
            tenant_id = token_user_id[6:]
        else:
            tenant_id = "tenant_default"
    is_platform_admin = (role in [ROLE_PLATFORM_ADMIN, ROLE_ADMIN])
    
    default_ids = {
        ROLE_PLATFORM_ADMIN: "admin_platform",
        ROLE_TENANT_ADMIN: "admin_tenant",
        ROLE_KNOWLEDGE_MASTER: "km_001",
        ROLE_SERVICE_AGENT: "agent_1028",
        ROLE_END_USER: "user_001",
        ROLE_USER: "user_001",
        ROLE_TECH_AGENT: "agent_1028",
        ROLE_ADMIN: "admin_master",
        ROLE_OPERATOR: "ops_001"
    }
    user_id = x_user_id or token_user_id or default_ids.get(role, "user_001")
    
    # 统一演示产品线与分组：除了平台超管外，统一置于 SAAS_CLOUD 产品组
    product_code = x_user_product
    assigned_kb_id = x_user_kb_id
    
    if role in [ROLE_SERVICE_AGENT, ROLE_TECH_AGENT] and not product_code:
        product_code = AGENT_PRODUCT_MAP.get(user_id, "SAAS_CLOUD")
        
    if role in [ROLE_KNOWLEDGE_MASTER, ROLE_OPERATOR]:
        if not assigned_kb_id:
            assigned_kb_id = OPERATOR_KB_MAP.get(user_id, None)
        if not product_code:
            product_code = OPERATOR_PRODUCT_MAP.get(user_id, "SAAS_CLOUD")

    if role in [ROLE_END_USER, ROLE_USER] and not product_code:
        product_code = "SAAS_CLOUD"

    name_map = {
        ROLE_PLATFORM_ADMIN: "SaaS平台超级管理员",
        ROLE_TENANT_ADMIN: f"企业租户管理员({user_id})",
        ROLE_KNOWLEDGE_MASTER: f"知识架构主管({user_id})",
        ROLE_SERVICE_AGENT: f"一线技术坐席({user_id})",
        ROLE_END_USER: f"终端客户·{user_id}",
        ROLE_USER: f"客户·{user_id}",
        ROLE_TECH_AGENT: f"技术客服专员({user_id})",
        ROLE_ADMIN: "系统超级管理员",
        ROLE_OPERATOR: f"知识运营专员({user_id})"
    }

    return CurrentUser(
        user_id=user_id,
        username=name_map.get(role, "未知用户"),
        role=role,
        tenant_id=tenant_id,
        is_platform_admin=is_platform_admin,
        product_code=product_code,
        assigned_kb_id=assigned_kb_id
    )

def require_roles(allowed_roles: List[str]):
    """角色权限拦截器 Dependency，支持两级五角色模型与旧角色别名兼容"""
    expanded_allowed: Set[str] = set()
    for r in allowed_roles:
        expanded_allowed.add(r)
        expanded_allowed.update(ROLE_ALIASES.get(r, set()))

    async def role_checker(
        authorization: Optional[str] = Header(default=None),
        x_user_role: Optional[str] = Header(default=None),
        x_role: Optional[str] = Header(default=None)
    ):
        raw_role = x_user_role or x_role
        if not raw_role and authorization and "Bearer " in authorization:
            token_str = authorization.replace("Bearer ", "").strip()
            for candidate_role in ALL_ROLES:
                if token_str.endswith(f"_{candidate_role}"):
                    raw_role = candidate_role
                    break
        current_role = raw_role.strip().lower() if raw_role else ROLE_ADMIN
        if current_role not in expanded_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：当前角色 [{current_role}] 无权访问该资源，需要角色: {allowed_roles}"
            )
        return current_role
    return role_checker
