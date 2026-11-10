from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.core.auth import (
    ROLE_ADMIN, 
    ROLE_TECH_AGENT, 
    ROLE_USER, 
    ROLE_OPERATOR,
    ROLE_PLATFORM_ADMIN,
    ROLE_TENANT_ADMIN,
    ROLE_KNOWLEDGE_MASTER,
    ROLE_SERVICE_AGENT,
    ROLE_END_USER,
    AGENT_PRODUCT_MAP,
    OPERATOR_KB_MAP,
    OPERATOR_PRODUCT_MAP,
    CurrentUser,
    get_current_user,
    USER_TENANT_MAP
)

router = APIRouter(prefix="/auth", tags=["用户认证与角色鉴权"])

class LoginRequest(BaseModel):
    username: str = Field(..., description="登录账号")
    password: str = Field(..., description="登录密码")

class UserRegisterRequest(BaseModel):
    username: str = Field(..., description="登录账号")
    password: str = Field(..., description="登录密码")
    account_type: Optional[str] = Field("end_user", description="账户类别: end_user (个人客户) 或 enterprise (企业用户)")
    company_name: Optional[str] = Field(None, description="企业全称（选填，用于订阅开通）")
    subdomain: Optional[str] = Field(None, description="期望子域名前缀（选填，如 zhike）")
    contact_name: Optional[str] = Field(None, description="联系人姓名（选填）")
    contact_phone: Optional[str] = Field(None, description="联系手机（选填）")
    credit_code: Optional[str] = Field(None, description="统一社会信用代码（选填）")
    industry: Optional[str] = Field("SaaS", description="所属行业（选填）")

class LoginResponse(BaseModel):
    user_id: str
    username: str
    role: str
    display_name: str
    token: str
    tenant_id: str = "tenant_default"
    tenant_name: str = "云创智能科技"
    is_platform_admin: bool = False
    product_code: Optional[str] = None
    group_name: Optional[str] = "云创云服务客服组"
    assigned_kb_id: Optional[str] = None
    enterprise_profile: Optional[Dict[str, Any]] = None

# 动态注册与新创建企业账号字典
REGISTERED_USERS: Dict[str, Dict[str, Any]] = {}

def register_user_credential(
    username: str,
    password: str,
    role: str = ROLE_END_USER,
    display_name: Optional[str] = None,
    tenant_id: str = "tenant_default",
    tenant_name: str = "云创智能科技",
    product_code: Optional[str] = "SAAS_CLOUD",
    group_name: Optional[str] = "云创云服务客服组",
    enterprise_profile: Optional[Dict[str, Any]] = None
):
    """注册或登记账号凭证，用于登录校验与多租户权限绑定"""
    clean_u = username.strip().lower()
    REGISTERED_USERS[clean_u] = {
        "passwords": [password, "123456", "admin123"],
        "role": role,
        "display_name": display_name or f"用户 · {username}",
        "user_id": clean_u,
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "product_code": product_code,
        "group_name": group_name,
        "assigned_kb_id": None,
        "enterprise_profile": enterprise_profile or {}
    }
    USER_TENANT_MAP[clean_u] = tenant_id

# 预置账号字典（除平台超管外，其余演示角色均归属于同一租户与产品分组：云创智能科技 · SAAS_CLOUD）
PRESET_USERS = {
    # 👑 SaaS 平台超级管理员（平台全局运营治理）
    "platform_admin": {
        "passwords": ["admin123", "123456", "platform_admin"],
        "role": ROLE_PLATFORM_ADMIN,
        "display_name": "👑 SaaS平台超级管理员",
        "user_id": "admin_platform",
        "tenant_id": "tenant_default",
        "product_code": None,
        "group_name": "平台全局治理组",
        "assigned_kb_id": None
    },
    # 🏢 企业租户管理员（所属分组：云创云服务客服组）
    "tenant_admin": {
        "passwords": ["admin123", "123456", "tenant_admin"],
        "role": ROLE_TENANT_ADMIN,
        "display_name": "🏢 企业租户管理员",
        "user_id": "admin_tenant",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    # 🧠 知识库架构主管（所属分组：云创云服务客服组）
    "knowledge_master": {
        "passwords": ["admin123", "km123", "123456", "ops123", "knowledge_master"],
        "role": ROLE_KNOWLEDGE_MASTER,
        "display_name": "🧠 知识库架构主管",
        "user_id": "km_001",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    # 👩‍💼 一线技术客服坐席（所属分组：云创云服务客服组）
    "service_agent": {
        "passwords": ["admin123", "agent123", "123456", "tech123", "service_agent"],
        "role": ROLE_SERVICE_AGENT,
        "display_name": "👩‍💼 一线技术客服坐席",
        "user_id": "agent_1028",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    # 👤 终端消费者 / 用户（所属分组：云创云服务客服组）
    "end_user": {
        "passwords": ["123456", "user123", "admin123", "end_user"],
        "role": ROLE_END_USER,
        "display_name": "👤 终端客户 · 张先生",
        "user_id": "user_001",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },

    # 兼容历史账号
    "admin": {
        "passwords": ["admin123", "123456", "admin"],
        "role": ROLE_ADMIN,
        "display_name": "系统超级管理员",
        "user_id": "admin_master",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    "tech": {
        "passwords": ["tech123", "123456", "tech"],
        "role": ROLE_TECH_AGENT,
        "display_name": "SaaS云平台技术客服(工号#1028)",
        "user_id": "agent_1028",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    "tech_ec": {
        "passwords": ["tech123", "123456", "tech", "agent123"],
        "role": ROLE_TECH_AGENT,
        "display_name": "电商系统技术客服(工号#1029)",
        "user_id": "agent_1029",
        "tenant_id": "tenant_default",
        "product_code": "E_COMMERCE",
        "group_name": "电商售后客服组",
        "assigned_kb_id": None
    },
    "tech_ecommerce": {
        "passwords": ["tech123", "123456", "tech", "agent123"],
        "role": ROLE_TECH_AGENT,
        "display_name": "电商系统技术客服(工号#1029)",
        "user_id": "agent_1029",
        "tenant_id": "tenant_default",
        "product_code": "E_COMMERCE",
        "group_name": "电商售后客服组",
        "assigned_kb_id": None
    },
    "agent": {
        "passwords": ["agent123", "123456", "agent"],
        "role": ROLE_TECH_AGENT,
        "display_name": "SaaS云平台技术客服(工号#1028)",
        "user_id": "agent_1028",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    "agent_1029": {
        "passwords": ["agent123", "123456", "agent", "tech123"],
        "role": ROLE_TECH_AGENT,
        "display_name": "电商系统技术客服(工号#1029)",
        "user_id": "agent_1029",
        "tenant_id": "tenant_default",
        "product_code": "E_COMMERCE",
        "group_name": "电商售后客服组",
        "assigned_kb_id": None
    },
    "ops": {
        "passwords": ["ops123", "123456", "ops"],
        "role": ROLE_OPERATOR,
        "display_name": "电商知识运营专员(工号#ops01)",
        "user_id": "ops_001",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    "operator": {
        "passwords": ["ops123", "123456", "operator"],
        "role": ROLE_OPERATOR,
        "display_name": "电商知识运营专员(工号#ops01)",
        "user_id": "ops_001",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    },
    "ops_saas": {
        "passwords": ["ops123", "123456", "ops"],
        "role": ROLE_OPERATOR,
        "display_name": "SaaS平台知识运营专员(工号#ops02)",
        "user_id": "ops_002",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": "kb_saas_cloud_02"
    },
    "user": {
        "passwords": ["user123", "123456", "user"],
        "role": ROLE_USER,
        "display_name": "普通客户·001",
        "user_id": "user_001",
        "tenant_id": "tenant_default",
        "product_code": "SAAS_CLOUD",
        "group_name": "云创云服务客服组",
        "assigned_kb_id": None
    }
}

# 注册别名快捷映射，保证使用角色名（如 tenant_admin）或展示用户名（如 admin_tenant, km_001）均可登录
PRESET_USERS["admin_tenant"] = PRESET_USERS["tenant_admin"]
PRESET_USERS["km_001"] = PRESET_USERS["knowledge_master"]
PRESET_USERS["agent_1028"] = PRESET_USERS["service_agent"]
PRESET_USERS["user_001"] = PRESET_USERS["end_user"]
PRESET_USERS["admin_platform"] = PRESET_USERS["platform_admin"]

@router.post("/login", response_model=LoginResponse, summary="多角色账号密码登录")
async def login(payload: LoginRequest):
    u = payload.username.strip().lower()
    p = payload.password.strip()

    if u in PRESET_USERS:
        conf = PRESET_USERS[u]
        if p in conf["passwords"]:
            tenant_id = conf.get("tenant_id", "tenant_default")
            is_platform_admin = (conf["role"] in [ROLE_PLATFORM_ADMIN, ROLE_ADMIN])
            tenant_name = "平台全局管理" if is_platform_admin else ("极速零售集团" if tenant_id == "tenant_retail_a" else "云创智能科技")
            return LoginResponse(
                user_id=conf["user_id"],
                username=u,
                role=conf["role"],
                display_name=conf["display_name"],
                token=f"token_{conf['user_id']}_{conf['role']}",
                tenant_id=tenant_id,
                tenant_name=tenant_name,
                is_platform_admin=is_platform_admin,
                product_code=conf.get("product_code", "SAAS_CLOUD"),
                group_name=conf.get("group_name", "云创云服务客服组"),
                assigned_kb_id=conf.get("assigned_kb_id"),
                enterprise_profile=conf.get("enterprise_profile")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码错误，请核对后重试"
            )

    if u in REGISTERED_USERS:
        conf = REGISTERED_USERS[u]
        if p in conf["passwords"]:
            tenant_id = conf.get("tenant_id", "tenant_default")
            is_platform_admin = (conf["role"] in [ROLE_PLATFORM_ADMIN, ROLE_ADMIN])
            return LoginResponse(
                user_id=conf["user_id"],
                username=u,
                role=conf["role"],
                display_name=conf["display_name"],
                token=f"mock_jwt_token_for_{u}_{conf['role']}",
                tenant_id=tenant_id,
                tenant_name=conf.get("tenant_name", "云创智能科技"),
                is_platform_admin=is_platform_admin,
                product_code=conf.get("product_code", "SAAS_CLOUD"),
                group_name=conf.get("group_name", "云创云服务客服组"),
                assigned_kb_id=conf.get("assigned_kb_id"),
                enterprise_profile=conf.get("enterprise_profile")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码错误，请核对后重试"
            )

    # 动态匹配：若账号包含 admin，视为管理员；ops/operator 视为运营；tech/agent 视为技术客服；其余视为客户
    product_code = "SAAS_CLOUD"
    assigned_kb_id = None
    group_name = "云创云服务客服组"
    if "admin" in u:
        role = ROLE_ADMIN
        display_name = f"管理员 · {u}"
        default_pwd = "admin123"
    elif "ops" in u or "operator" in u:
        role = ROLE_OPERATOR
        assigned_kb_id = OPERATOR_KB_MAP.get(u, None)
        product_code = OPERATOR_PRODUCT_MAP.get(u, "SAAS_CLOUD")
        display_name = f"知识运营 · {u}"
        default_pwd = "ops123"
    elif "tech" in u or "agent" in u:
        role = ROLE_TECH_AGENT
        product_code = AGENT_PRODUCT_MAP.get(u, "SAAS_CLOUD")
        display_name = f"技术客服 · {u} ({product_code})"
        default_pwd = "tech123"
    else:
        role = ROLE_USER
        display_name = f"普通客户 · {u}"
        default_pwd = "123456"

    if p in [default_pwd, "123456", u]:
        is_platform_admin = (role == ROLE_ADMIN)
        return LoginResponse(
            user_id=u,
            username=u,
            role=role,
            display_name=display_name,
            token=f"token_{u}_{role}",
            tenant_id="tenant_default",
            tenant_name="平台全局管理" if is_platform_admin else "云创智能科技",
            is_platform_admin=is_platform_admin,
            product_code=product_code,
            group_name=group_name,
            assigned_kb_id=assigned_kb_id
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="账号或密码错误。预置账号：admin/admin123, tenant_admin/admin123, km/km123, agent/agent123, user/user123"
    )

@router.post("/register", response_model=LoginResponse, summary="普通用户注册（带企业订阅选填项）")
async def register(payload: UserRegisterRequest):
    u = payload.username.strip().lower()
    p = payload.password.strip()
    if not u or len(u) < 2:
        raise HTTPException(status_code=400, detail="用户名长度不能少于2位")
    if not p or len(p) < 4:
        raise HTTPException(status_code=400, detail="密码长度不能少于4位")
    if u in PRESET_USERS or u in REGISTERED_USERS:
        raise HTTPException(status_code=400, detail="该用户名已存在，请尝试其他账号或直接登录")
    
    ent_profile = {
        "company_name": payload.company_name.strip() if payload.company_name else None,
        "subdomain": payload.subdomain.strip().lower() if payload.subdomain else None,
        "contact_name": payload.contact_name.strip() if payload.contact_name else None,
        "contact_phone": payload.contact_phone.strip() if payload.contact_phone else None,
        "credit_code": payload.credit_code.strip() if payload.credit_code else None,
        "industry": payload.industry or "SaaS"
    }

    is_enterprise = (payload.account_type == "enterprise") or bool(payload.company_name and payload.company_name.strip())
    assigned_role = ROLE_TENANT_ADMIN if is_enterprise else ROLE_END_USER
    tenant_name = payload.company_name.strip() if (payload.company_name and payload.company_name.strip()) else "云创智能科技"
    display_name = f"企管 · {payload.contact_name or u}" if is_enterprise else f"客户 · {payload.contact_name or u}"

    register_user_credential(
        username=u,
        password=p,
        role=assigned_role,
        display_name=display_name,
        tenant_id="tenant_default",
        tenant_name=tenant_name,
        product_code="SAAS_CLOUD",
        group_name="云创企业服务组" if is_enterprise else "云创云服务客服组",
        enterprise_profile=ent_profile
    )

    return LoginResponse(
        user_id=u,
        username=u,
        role=assigned_role,
        display_name=display_name,
        token=f"mock_jwt_token_for_{u}_{assigned_role}",
        tenant_id="tenant_default",
        tenant_name=tenant_name,
        is_platform_admin=False,
        product_code="SAAS_CLOUD",
        group_name="云创企业服务组" if is_enterprise else "云创云服务客服组",
        enterprise_profile=ent_profile
    )

@router.get("/me", response_model=LoginResponse, summary="获取当前登录用户详情与企业画像")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    u = current_user.user_id.lower()
    conf = REGISTERED_USERS.get(u) or PRESET_USERS.get(u, {})
    return LoginResponse(
        user_id=current_user.user_id,
        username=current_user.user_id,
        role=current_user.role,
        display_name=current_user.username,
        token=f"mock_jwt_token_for_{current_user.user_id}_{current_user.role}",
        tenant_id=current_user.tenant_id,
        tenant_name="平台全局管理" if current_user.is_platform_admin else "企业空间",
        is_platform_admin=current_user.is_platform_admin,
        product_code=current_user.product_code,
        group_name="云创云服务客服组",
        assigned_kb_id=current_user.assigned_kb_id,
        enterprise_profile=conf.get("enterprise_profile")
    )
