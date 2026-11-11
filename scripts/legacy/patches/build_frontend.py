<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>智能客服系统 - 多角色权限与知识库工作台</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Vue 3 -->
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <style>
    [v-cloak] { display: none; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f8fafc; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
  </style>
</head>
<body class="bg-slate-100 text-slate-800 font-sans antialiased h-screen overflow-hidden">
  <div id="app" v-cloak class="h-screen w-screen overflow-hidden">

    <!-- ================= 0. 全屏现代化登录页面 ================= -->
    <div v-if="!isLoggedIn" class="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 p-6 relative overflow-hidden select-none">
      <!-- 背景光晕装饰 -->
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-sky-500/20 rounded-full blur-3xl pointer-events-none"></div>

      <div class="w-full max-w-xl bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl text-white relative z-10 space-y-6">
        
        <!-- 登录头部 -->
        <div class="text-center space-y-2">
          <div class="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-indigo-500/30">
            🤖
          </div>
          <h1 class="text-2xl font-bold tracking-tight text-white">智能客服知识库系统</h1>
          <p class="text-xs text-slate-300">多产品隔离 · 智能问答与业务闭环 · 角色专属工作台</p>
        </div>

        <!-- 错误提示 -->
        <div v-if="loginError" class="bg-rose-500/20 border border-rose-500/40 text-rose-200 text-xs px-3.5 py-2.5 rounded-xl flex items-center gap-2">
          <span>⚠️</span>
          <span>{{ loginError }}</span>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleLoginSubmit" class="space-y-4 text-xs">
          <div>
            <label class="block font-medium text-slate-300 mb-1.5">登录账号</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 pointer-events-none">👤</span>
              <input 
                v-model="loginForm.username" 
                type="text" 
                required 
                placeholder="请输入用户名 (如 admin / tech / user)" 
                class="w-full bg-slate-900/60 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
              />
            </div>
          </div>

          <div>
            <label class="block font-medium text-slate-300 mb-1.5">登录密码</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 pointer-events-none">🔒</span>
              <input 
                v-model="loginForm.password" 
                type="password" 
                required 
                placeholder="请输入密码" 
                class="w-full bg-slate-900/60 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
              />
            </div>
          </div>

          <button 
            type="submit" 
            :disabled="loginLoading"
            class="w-full bg-gradient-to-r from-indigo-500 to-sky-500 hover:from-indigo-600 hover:to-sky-600 text-white font-semibold py-2.5 rounded-xl shadow-lg shadow-indigo-500/25 transition disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
          >
            <span v-if="loginLoading" class="animate-spin">⏳</span>
            <span>{{ loginLoading ? '正在验证身份...' : '登 录 系 统' }}</span>
          </button>
        </form>

        <!-- 快捷登录体验入口 -->
        <div class="pt-4 border-t border-white/10 text-xs">
          <p class="text-[11px] text-slate-400 font-medium mb-2.5 text-center">快捷体验账号（一键填入并登录）</p>
          <div class="grid grid-cols-5 gap-2">
            <button 
              type="button" 
              @click="quickFillLogin('admin', 'admin123')"
              class="bg-white/5 hover:bg-white/15 border border-white/10 rounded-xl p-2 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👑</div>
              <div class="font-bold text-white text-[11px] mt-1">超级管理员</div>
              <div class="text-[9px] text-slate-400 font-mono">admin / admin123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('ops', 'ops123')"
              class="bg-white/5 hover:bg-rose-500/20 border border-rose-500/30 rounded-xl p-2 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">🚨</div>
              <div class="font-bold text-rose-300 text-[11px] mt-1">电商运营</div>
              <div class="text-[9px] text-slate-400 font-mono">ops / ops123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('tech', 'tech123')"
              class="bg-white/5 hover:bg-amber-500/20 border border-amber-500/30 rounded-xl p-2 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👩‍💼</div>
              <div class="font-bold text-amber-200 text-[11px] mt-1">SaaS客服</div>
              <div class="text-[9px] text-slate-400 font-mono">tech / tech123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('tech_ec', 'tech123')"
              class="bg-white/5 hover:bg-sky-500/20 border border-sky-500/30 rounded-xl p-2 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👨‍💻</div>
              <div class="font-bold text-sky-200 text-[11px] mt-1">电商客服</div>
              <div class="text-[9px] text-slate-400 font-mono">tech_ec / tech123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('user', 'user123')"
              class="bg-white/5 hover:bg-white/15 border border-white/10 rounded-xl p-2 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👤</div>
              <div class="font-bold text-white text-[11px] mt-1">普通用户</div>
              <div class="text-[9px] text-slate-400 font-mono">user / user123</div>
            </button>
          </div>
          <div class="mt-2 text-center text-[10px] text-slate-400">
            * 另有 SaaS知识运营账号: <span class="text-indigo-300 font-mono">ops_saas / 123456</span> 体验多组知识库运营权限隔离
          </div>
        </div>

      </div>
    </div>

    <!-- ================= 登录后的主工作台 ================= -->
    <div v-else class="flex h-screen w-full relative">

      <!-- 客服专员新客户分配实时提醒 Toast 弹窗 -->
      <div v-if="newAssignmentAlert" class="fixed top-5 right-5 z-50 bg-white border border-indigo-200 shadow-2xl rounded-2xl p-4 max-w-sm animate-bounce duration-500 flex items-start gap-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-lg flex-shrink-0">
          🔔
        </div>
        <div class="flex-1 min-w-0">
          <h4 class="text-xs font-bold text-slate-900">新客户接入分配提醒！</h4>
          <p class="text-[11px] text-slate-600 mt-1">
            客户 <strong class="text-indigo-600">{{ newAssignmentAlert.customer_name }}</strong> 发起了人工咨询需求（产品: {{ newAssignmentAlert.product_code }}）。
          </p>
          <div class="flex items-center gap-2 mt-2.5">
            <button @click="handleJumpToAssignedSession(newAssignmentAlert)" class="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-[11px] font-bold transition cursor-pointer">
              立即跳转接听
            </button>
            <button @click="newAssignmentAlert = null" class="px-2 py-1 text-slate-400 hover:text-slate-600 text-[11px] cursor-pointer">
              稍后处理
            </button>
          </div>
        </div>
      </div>

      <!-- ================= 1. 左侧统一主菜单栏 (受角色权限管控) ================= -->
      <aside class="w-64 bg-slate-900 text-slate-200 flex flex-col flex-shrink-0 border-r border-slate-800 select-none">
        
        <!-- 品牌与当前角色标识 -->
        <div class="h-16 flex items-center px-5 gap-3 border-b border-slate-800 bg-slate-950/60">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-500/20 text-xs">
            CS
          </div>
          <div class="flex-1 min-w-0">
            <h1 class="text-xs font-bold tracking-wide text-white leading-tight truncate">智能客服系统</h1>
            <p class="text-[10px] text-slate-400 font-mono flex items-center gap-1 mt-0.5">
              <span class="w-1.5 h-1.5 rounded-full" :class="currentRole === 'admin' ? 'bg-rose-400' : (currentRole === 'operator' ? 'bg-orange-400' : (currentRole === 'tech_agent' ? 'bg-amber-400' : 'bg-emerald-400'))"></span>
              <span>{{ roleLabel }}工作台</span>
            </p>
          </div>
        </div>

        <!-- 导航链接：根据三种角色严格区分可见性 -->
        <nav class="flex-1 px-3 py-4 space-y-1.5">
          
          <!-- 菜单 1: AI客服对话 (普通用户、技术客服、超级管理员均可见) -->
          <button 
            v-if="hasMenuPermission('chat')"
            @click="activeMenu = 'chat'" 
            :class="activeMenu === 'chat' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition duration-150 text-left cursor-pointer"
          >
            <span class="text-base">🤖</span>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span>AI客服对话</span>
                <span class="text-[9px] bg-emerald-500/30 text-emerald-200 px-1.5 py-0.2 rounded-full font-mono">通用</span>
              </div>
              <p class="text-[10px] opacity-75 mt-0.5 font-normal">
                {{ currentRole === 'user' ? '在线智能答疑' : '客户进线接待与工单协同' }}
              </p>
            </div>
          </button>

          <!-- 菜单 2: 知识库管理 (仅 超级管理员 可见) -->
          <button 
            v-if="hasMenuPermission('kb')"
            @click="activeMenu = 'kb'" 
            :class="activeMenu === 'kb' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition duration-150 text-left cursor-pointer"
          >
            <span class="text-base">📚</span>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span>知识库管理</span>
                <span class="text-[9px] bg-rose-500/30 text-rose-200 px-1.5 py-0.2 rounded-full font-mono">超管专属</span>
              </div>
              <p class="text-[10px] opacity-75 mt-0.5 font-normal">多产品隔离与检索阈值治理</p>
            </div>
          </button>

          <!-- 菜单 3: 知识文档与片段治理 (运营、技术客服与超管可见) -->
          <button 
            v-if="hasMenuPermission('chunks')"
            @click="activeMenu = 'chunks'" 
            :class="activeMenu === 'chunks' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition duration-150 text-left cursor-pointer"
          >
            <span class="text-base">🧩</span>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span>知识文档管理</span>
                <span class="text-[9px] bg-amber-500/30 text-amber-200 px-1.5 py-0.2 rounded-full font-mono">{{ currentRole === 'operator' ? '运营专属' : (currentRole === 'admin' ? '超管审核' : '客服提交') }}</span>
              </div>
              <p class="text-[10px] opacity-75 mt-0.5 font-normal">
                {{ currentRole === 'operator' ? '负责知识库文档/FAQ/切片管理' : (currentRole === 'admin' ? '全域文档审核/切片管理/版本回滚' : '本产品文档提交/切片查阅') }}
              </p>
            </div>
          </button>

          <!-- 菜单 4: BadCase 治理池 (超管 与 运营专员 可见) -->
          <button 
            v-if="hasMenuPermission('badcases')"
            @click="activeMenu = 'badcases'" 
            :class="activeMenu === 'badcases' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition duration-150 text-left cursor-pointer"
          >
            <span class="text-base">🚨</span>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span>BadCase 治理池</span>
                <span class="text-[9px] bg-rose-500/30 text-rose-200 px-1.5 py-0.2 rounded-full font-mono">运营/超管</span>
              </div>
              <p class="text-[10px] opacity-75 mt-0.5 font-normal">
                {{ currentRole === 'admin' ? '全域低质问答归因 · 语义聚类与效果回归' : '本库差评归因 · 相似问追加与FAQ沉淀' }}
              </p>
            </div>
          </button>
        </nav>

        <!-- 底部：当前登录用户身份卡片 & 退出登录按钮 -->
        <div class="p-3.5 border-t border-slate-800/80 bg-slate-950/60 space-y-3">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm"
                 :class="currentRole === 'admin' ? 'bg-rose-600 text-white' : (currentRole === 'operator' ? 'bg-orange-600 text-white' : (currentRole === 'tech_agent' ? 'bg-amber-600 text-white' : 'bg-indigo-600 text-white'))">
              {{ currentRole === 'admin' ? '👑' : (currentRole === 'operator' ? '🚨' : (currentRole === 'tech_agent' ? '👩‍💼' : '👤')) }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-bold text-white truncate">{{ currentUserDisplayName }}</p>
              <p class="text-[10px] text-slate-400 font-mono truncate">
                账号: {{ currentUsername }} <span v-if="currentRole === 'operator'" class="text-orange-300 font-semibold truncate">({{ assignedKbName }})</span><span v-else-if="currentUserProduct" class="text-indigo-400 font-semibold">({{ currentUserProduct }})</span>
              </p>
            </div>
          </div>
          <button 
            @click="handleLogout"
            class="w-full flex items-center justify-center gap-1.5 py-2 bg-slate-800/80 hover:bg-rose-950/60 hover:text-rose-300 text-slate-300 border border-slate-700/60 hover:border-rose-800/60 rounded-xl text-xs font-medium transition cursor-pointer"
          >
            <span>🚪</span>
            <span>退出当前账号</span>
          </button>
        </div>
      </aside>

      <!-- ================= 2. 主体工作区 ================= -->
      <main class="flex-1 flex flex-col h-screen overflow-hidden bg-white">

        <!-- ================= 模块 1: AI客服对话 ================= -->
        <section v-if="activeMenu === 'chat'" class="flex-1 flex h-full overflow-hidden">
          
          <!-- 2.1 客户会话列表 (仅 技术客服 和 超管 可见；普通用户删除对话列表，每次开新对话) -->
          <div v-if="currentRole !== 'user'" class="w-72 border-r border-slate-200 bg-slate-50 flex flex-col h-full flex-shrink-0">
            <div class="p-4 border-b border-slate-200 bg-white space-y-2">
              <div class="flex items-center justify-between">
                <div>
                  <span class="text-xs font-bold uppercase tracking-wider text-slate-800">
                    {{ currentRole === 'admin' ? '全渠道客户会话' : '分配给我的待办会话' }}
                  </span>
                  <p class="text-[10px] text-slate-400">
                    {{ currentRole === 'admin' ? `共 ${filteredSessions.length} 条会话记录` : `当前负责 ${filteredSessions.length} 位进线客户` }}
                  </p>
                </div>
                <!-- 超管可手动新建客户会话 -->
                <button 
                  v-if="currentRole === 'admin'"
                  @click="showNewSessionModal = true" 
                  class="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 px-2.5 py-1 rounded-lg font-semibold transition cursor-pointer"
                >
                  + 新会话
                </button>
              </div>

              <!-- 超管端历史状态过滤（全部 / 活跃中 / 已结单历史） -->
              <div v-if="currentRole === 'admin'" class="grid grid-cols-3 gap-1 bg-slate-100 p-0.5 rounded-lg text-[10px]">
                <button 
                  @click="sessionFilterStatus = 'ACTIVE'" 
                  :class="sessionFilterStatus === 'ACTIVE' ? 'bg-white font-bold text-indigo-600 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
                  class="py-1 rounded-md transition text-center"
                >
                  进行中
                </button>
                <button 
                  @click="sessionFilterStatus = 'CLOSED'" 
                  :class="sessionFilterStatus === 'CLOSED' ? 'bg-white font-bold text-indigo-600 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
                  class="py-1 rounded-md transition text-center"
                >
                  已结单历史
                </button>
                <button 
                  @click="sessionFilterStatus = 'ALL'" 
                  :class="sessionFilterStatus === 'ALL' ? 'bg-white font-bold text-indigo-600 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
                  class="py-1 rounded-md transition text-center"
                >
                  全部
                </button>
              </div>
            </div>

            <!-- 会话项列表 -->
            <div class="flex-1 overflow-y-auto p-2 space-y-1.5">
              <div 
                v-for="s in filteredSessions" 
                :key="s.id"
                @click="switchSession(s)"
                :class="currentSession && currentSession.id === s.id ? 'bg-indigo-50 border-indigo-300 shadow-xs' : 'bg-white border-slate-200 hover:bg-slate-100/70'"
                class="p-3 rounded-xl border transition cursor-pointer"
              >
                <div class="flex items-center gap-2.5">
                  <div class="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-xs flex-shrink-0">
                    {{ (s.customer_name || '客').slice(0, 1) }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <p class="text-xs font-bold text-slate-800 truncate">{{ s.customer_name }}</p>
                      <span class="text-[10px] font-mono text-slate-400">{{ (s.last_message_at || '').slice(11, 16) }}</span>
                    </div>
                    <div class="flex items-center justify-between mt-1">
                      <p class="text-[11px] text-slate-500 truncate mr-2">{{ s.last_message || '新建立会话' }}</p>
                      <span 
                        v-if="s.status === 'HUMAN_CONNECTED'" 
                        class="text-[9px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded font-bold whitespace-nowrap animate-pulse"
                      >
                        人工接管
                      </span>
                      <span 
                        v-else-if="s.status === 'CLOSED'" 
                        class="text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.2 rounded font-medium whitespace-nowrap"
                      >
                        已结单
                      </span>
                      <span 
                        v-else 
                        class="text-[9px] bg-emerald-50 text-emerald-700 px-1.5 py-0.2 rounded font-medium whitespace-nowrap"
                      >
                        AI服务
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="filteredSessions.length === 0" class="p-8 text-center text-xs text-slate-400">
                暂无分配的会话记录
              </div>
            </div>

            <!-- 技术客服负责产品标识 -->
            <div v-if="currentRole === 'tech_agent'" class="p-3 border-t border-slate-200 bg-white text-xs text-slate-500">
              <span class="font-semibold text-slate-700">负责业务线:</span>
              <span class="ml-1 px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono font-bold">{{ currentUserProduct || 'SAAS_CLOUD' }}</span>
            </div>
          </div>

          <!-- 2.2 聊天对话主视窗 -->
          <div class="flex-1 flex flex-col h-full bg-slate-100/60 overflow-hidden relative">
            
            <!-- 顶部状态栏 -->
            <div class="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-2xs z-10">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full flex items-center justify-center text-xs shadow-sm"
                     :class="currentRole === 'user' ? 'bg-gradient-to-tr from-indigo-500 to-sky-400 text-white font-bold' : 'bg-indigo-600 text-white font-bold'">
                  {{ currentRole === 'user' ? '🤖' : (currentSession?.customer_name || '客').slice(0, 1) }}
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <h2 class="text-sm font-bold text-slate-900">
                      {{ currentRole === 'user' ? 'AI 智能客服在线助手' : (currentSession?.customer_name || '客户对话') }}
                    </h2>
                    <span 
                      v-if="currentSession?.status === 'HUMAN_CONNECTED'"
                      class="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-semibold flex items-center gap-1"
                    >
                      <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping"></span>
                      人工客服座席接入中 (工号: {{ currentSession?.assigned_agent || '客服专员' }})
                    </span>
                    <span 
                      v-else-if="currentSession?.status === 'CLOSED'"
                      class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200 font-semibold"
                    >
                      已结单历史
                    </span>
                    <span 
                      v-else
                      class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold flex items-center gap-1"
                    >
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      AI智能应答模式
                    </span>
                  </div>
                  <p class="text-[11px] text-slate-400 font-mono">
                    {{ currentRole === 'user' ? '在线企业客服 · 专属新会话已开启' : `客户ID: ${currentSession?.customer_id} | 产品: ${currentSession?.product_code}` }}
                  </p>
                </div>
              </div>

              <!-- 右侧快捷操作栏：根据角色权限区分 -->
              <div class="flex items-center gap-2">
                <!-- 普通用户咨询产品线选择切换 -->
                <div v-if="currentRole === 'user'" class="flex items-center gap-1.5 mr-2">
                  <span class="text-[11px] text-slate-500 font-medium">咨询产品:</span>
                  <select v-model="currentProductCode" @change="onUserProductChange" class="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-semibold text-slate-700">
                    <option value="SAAS_CLOUD">企业SaaS云平台</option>
                    <option value="E_COMMERCE">电商零售系统</option>
                    <option value="FIN_AI">金融智能助手</option>
                  </select>
                </div>

                <!-- 普通用户在人工接入模式下：显眼的挂断人工服务按钮 -->
                <button 
                  v-if="currentRole === 'user' && currentSession?.status === 'HUMAN_CONNECTED'"
                  @click="handleUserHangup" 
                  class="text-xs bg-rose-600 hover:bg-rose-700 text-white font-bold px-3.5 py-1.5 rounded-xl transition shadow-md shadow-rose-500/20 flex items-center gap-1 cursor-pointer"
                >
                  <span>🔴</span>
                  <span>挂断人工服务</span>
                </button>

                <!-- 普通用户在 AI 模式下可点击【转接人工客服】（常驻支持二次转人工） -->
                <button 
                  v-if="currentRole === 'user' && currentSession?.status !== 'HUMAN_CONNECTED'"
                  @click="handleManualTransferHuman" 
                  class="text-xs bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 px-3 py-1.5 rounded-lg font-semibold transition flex items-center gap-1 cursor-pointer"
                >
                  <span>👩‍💼</span>
                  <span>转接人工客服</span>
                </button>

                <!-- 技术客服 或 超管 有权点击【结束人工切回AI】 -->
                <button 
                  v-if="canManageHumanSession && currentSession?.status === 'HUMAN_CONNECTED'"
                  @click="finishHumanService" 
                  class="text-xs bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer"
                >
                  结束人工，切回AI
                </button>

                <!-- 技术客服 或 超管 可以在 AI 状态下一键主动【接入接管会话】 -->
                <button 
                  v-if="canManageHumanSession && currentSession?.status !== 'HUMAN_CONNECTED'"
                  @click="handleManualTransferHuman" 
                  class="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-lg font-semibold transition flex items-center gap-1 cursor-pointer"
                >
                  <span>🎧</span>
                  <span>座席主动接管</span>
                </button>
              </div>
            </div>

            <!-- 消息流展示区域 -->
            <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-5">
              
              <!-- 欢迎提示语 -->
              <div class="flex gap-3 max-w-2xl">
                <div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm">
                  AI
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-4 text-xs text-slate-700 shadow-2xs leading-relaxed">
                  <p class="font-bold text-slate-900 text-sm mb-1">您好！{{ currentUserDisplayName }}</p>
                  <p>我是您的专属智能客服助手，已接入当前业务产品（{{ currentProductCode }}）知识库与智能检索系统。您可以随时向我咨询功能指南、业务政策，或在需要时转接技术客服：</p>
                  
                  <div class="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-100">
                    <button @click="sendQuickPrompt('怎么退款')" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] px-2.5 py-1 rounded-full transition cursor-pointer">
                      👉 怎么退款 (知识库直接回答)
                    </button>
                    <button @click="sendQuickPrompt('查我的订单物流到哪了')" class="bg-sky-50 hover:bg-sky-100 text-sky-700 text-[11px] px-2.5 py-1 rounded-full transition font-semibold cursor-pointer">
                      📦 查订单物流 (业务卡片驱动)
                    </button>
                    <button @click="sendQuickPrompt('查我的退款进度')" class="bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-[11px] px-2.5 py-1 rounded-full transition font-semibold cursor-pointer">
                      💰 查退款进度 (售后单查询)
                    </button>
                    <button @click="sendQuickPrompt('人工客服在哪里')" class="bg-amber-50 hover:bg-amber-100 text-amber-700 text-[11px] px-2.5 py-1 rounded-full transition cursor-pointer">
                      👩‍💼 转人工客服专员
                    </button>
                  </div>
                </div>
              </div>

              <!-- 动态消息流 -->
              <div 
                v-for="(m, idx) in messageList" 
                :key="m.id || idx" 
                class="flex gap-3"
                :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
              >
                <!-- 头像：系统/助手/人工客服 -->
                <div 
                  v-if="m.role !== 'user'" 
                  class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-sm"
                  :class="m.role === 'human_agent' ? 'bg-amber-600 text-white' : (m.role === 'system' ? 'bg-slate-600 text-white' : 'bg-indigo-600 text-white')"
                >
                  {{ m.role === 'human_agent' ? '👩‍💼' : (m.role === 'system' ? '🔔' : 'AI') }}
                </div>

                <!-- 消息气泡卡片 -->
                <div 
                  class="max-w-2xl rounded-2xl p-4 text-xs shadow-2xs space-y-3"
                  :class="m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : (m.role === 'system' ? 'bg-slate-100 text-slate-700 border border-slate-200 rounded-tl-sm w-full text-center py-2.5' : (m.role === 'human_agent' ? 'bg-amber-50/70 border border-amber-200 text-slate-800 rounded-tl-sm' : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm'))"
                >
                  <!-- 头部标记 -->
                  <div v-if="m.role !== 'user' && m.role !== 'system'" class="flex items-center justify-between text-[11px] pb-1 border-b border-slate-100">
                    <span class="font-bold flex items-center gap-1" :class="m.role === 'human_agent' ? 'text-amber-800' : 'text-indigo-700'">
                      <span>{{ m.role === 'human_agent' ? '👨‍💻 人工客服专员' : '🤖 智能助手应答' }}</span>
                      <span v-if="m.confidence_score" class="font-mono text-[10px] bg-slate-100 px-1.5 py-0.2 rounded-full text-slate-600">
                        置信度: {{ (m.confidence_score * 100).toFixed(0) }}%
                      </span>
                    </span>
                    <span class="text-slate-400 font-mono text-[10px]">{{ (m.created_at || '').slice(11, 16) }}</span>
                  </div>

                  <!-- 消息主体正文 -->
                  <div class="leading-relaxed whitespace-pre-wrap select-text">
                    {{ m.content }}
                  </div>

                  <!-- 业务卡片展示 -->
                  <div v-if="m.business_data" class="pt-2 border-t border-slate-100">
                    <div v-if="m.business_data.card_type === 'ORDER_CARD'" class="bg-indigo-50/60 p-3 rounded-xl border border-indigo-200 text-slate-800 space-y-2">
                      <div class="flex items-center justify-between font-bold text-xs">
                        <span class="text-indigo-900">📦 订单详情 (#{{ m.business_data.order_id }})</span>
                        <span class="text-indigo-600 font-mono">{{ m.business_data.status }}</span>
                      </div>
                      <div class="text-[11px] space-y-1 text-slate-600">
                        <p><strong>商品:</strong> {{ m.business_data.item_name }} ({{ m.business_data.amount }})</p>
                        <p><strong>快递公司:</strong> {{ m.business_data.carrier }} · 单号: {{ m.business_data.tracking_no }}</p>
                        <p><strong>最新轨迹:</strong> {{ m.business_data.latest_track }}</p>
                      </div>
                    </div>

                    <div v-else-if="m.business_data.card_type === 'REFUND_CARD'" class="bg-emerald-50/60 p-3 rounded-xl border border-emerald-200 text-slate-800 space-y-2">
                      <div class="flex items-center justify-between font-bold text-xs">
                        <span class="text-emerald-900">💰 售后退款单 (#{{ m.business_data.refund_id }})</span>
                        <span class="text-emerald-600 font-bold">{{ m.business_data.status }}</span>
                      </div>
                      <div class="text-[11px] space-y-1 text-slate-600">
                        <p><strong>退款金额:</strong> {{ m.business_data.amount }} (原路退回)</p>
                        <p><strong>申请原因:</strong> {{ m.business_data.reason }}</p>
                        <p><strong>审核意见:</strong> {{ m.business_data.review_comment }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- 相似推荐卡片 -->
                  <div v-if="m.suggested_questions && m.suggested_questions.length > 0" class="space-y-1.5 pt-2 border-t border-slate-100">
                    <div class="flex flex-wrap gap-2">
                      <button 
                        v-for="sq in m.suggested_questions" 
                        :key="sq.question_id"
                        @click="sendQuickPrompt(sq.title)"
                        class="text-left text-xs bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-200 hover:border-indigo-300 px-3 py-1.5 rounded-xl transition flex items-center gap-1.5 cursor-pointer"
                      >
                        <span class="text-indigo-500 font-bold">❓</span>
                        <span>{{ sq.title }}</span>
                      </button>
                    </div>
                  </div>

                  <!-- 知识来源引用 (点击唤出切片抽屉) -->
                  <div v-if="m.sources && m.sources.length > 0" class="pt-2 border-t border-slate-100">
                    <div class="flex items-center justify-between text-[11px]">
                      <span class="font-bold text-indigo-700">📚 知识库溯源支撑 ({{ m.sources.length }} 条)</span>
                      <span class="text-[10px] text-slate-400">点击查阅知识切片</span>
                    </div>
                    <div class="grid grid-cols-1 gap-1.5 mt-2">
                      <div 
                        v-for="(src, sidx) in m.sources" 
                        :key="sidx"
                        @click="openSourceDrawer(src)"
                        class="bg-slate-50 hover:bg-indigo-50/70 p-2 rounded-lg border border-slate-200 hover:border-indigo-200 cursor-pointer transition flex items-center justify-between text-slate-700"
                      >
                        <div class="flex items-center gap-2 truncate">
                          <span class="w-4 h-4 rounded-full bg-indigo-200 text-indigo-800 text-[10px] font-bold flex items-center justify-center flex-shrink-0">{{ sidx + 1 }}</span>
                          <span class="font-semibold text-xs text-slate-900 truncate">{{ src.doc_name }}</span>
                          <span class="text-[10px] text-slate-500">({{ src.heading || '正文切片' }})</span>
                        </div>
                        <span class="text-indigo-600 text-xs font-semibold ml-2">查阅 ➔</span>
                      </div>
                    </div>
                  </div>

                  <!-- AI 回答质量评价与人工标错 (全生命周期多维采集入口) -->
                  <div v-if="m.role === 'assistant'" class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                    <div class="flex items-center gap-1.5">
                      <span class="text-slate-400 text-[10px]">回答反馈:</span>
                      <button 
                        @click="handleThumbUp(m)"
                        class="px-2 py-0.5 rounded-md border text-[10px] transition flex items-center gap-1 cursor-pointer"
                        :class="m.user_rated === 'UP' ? 'bg-emerald-100 border-emerald-300 text-emerald-800 font-bold' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-emerald-50 hover:text-emerald-700'"
                      >
                        <span>👍</span>
                        <span>有帮助</span>
                      </button>
                      <button 
                        @click="openFeedbackModal(m)"
                        class="px-2 py-0.5 rounded-md border text-[10px] transition flex items-center gap-1 cursor-pointer"
                        :class="m.user_rated === 'DOWN' ? 'bg-rose-100 border-rose-300 text-rose-800 font-bold' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-rose-50 hover:text-rose-700'"
                      >
                        <span>👎</span>
                        <span>不满意</span>
                      </button>
                    </div>

                    <!-- 坐席/管理员 人工标错入口 -->
                    <div v-if="currentRole === 'tech_agent' || currentRole === 'admin'">
                      <button 
                        @click="openAgentLabelModal(m)"
                        class="px-2 py-0.5 rounded-md bg-amber-50 border border-amber-200 text-amber-800 hover:bg-amber-100 text-[10px] font-semibold transition flex items-center gap-1 cursor-pointer"
                      >
                        <span>🏷️</span>
                        <span>标为BadCase</span>
                      </button>
                    </div>
                  </div>

                  <!-- 底部常驻转人工按钮 (普通用户在 AI 模式下可见，挂断后立刻可再次使用) -->
                  <div v-if="currentRole === 'user' && m.role === 'assistant' && currentSession?.status !== 'HUMAN_CONNECTED'" class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                    <span class="text-slate-400">解答不够满意？可随时请求人工协助</span>
                    <button 
                      @click="handleManualTransferHuman" 
                      class="bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-lg font-semibold transition flex items-center gap-1 cursor-pointer"
                    >
                      <span>👩‍💼</span>
                      <span>转接专属技术客服</span>
                    </button>
                  </div>

                </div>
              </div>

              <!-- 加载状态 -->
              <div v-if="isThinking" class="flex gap-3 items-center text-xs text-slate-500">
                <div class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold animate-pulse">
                  AI
                </div>
                <div class="bg-white px-4 py-2.5 rounded-2xl border border-slate-200 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>
                  <span>正在执行 Query 改写、BM25与向量双路召回及重排决策...</span>
                </div>
              </div>

            </div>

            <!-- 底部发送框 -->
            <div class="p-4 bg-white border-t border-slate-200">
              <div class="flex gap-2">
                <input 
                  v-model="inputQuery" 
                  @keyup.enter="handleSend"
                  type="text" 
                  :placeholder="currentRole === 'user' ? '请输入您的问题（如：怎么退款、查我的订单物流、重置密码...）' : '以人工客服身份输入解答或指导意见...'" 
                  class="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
                />
                <button 
                  @click="handleSend" 
                  :disabled="!inputQuery.trim() || isThinking"
                  class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-6 py-2.5 rounded-xl transition shadow-md shadow-indigo-500/25 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center gap-1"
                >
                  <span>发送</span>
                  <span>➔</span>
                </button>
              </div>
            </div>

          </div>
        </section>

        <!-- ================= 模块 2: 知识片段与文档治理 ================= -->
        <section v-if="activeMenu === 'chunks' && hasMenuPermission('chunks')" class="flex-1 overflow-y-auto p-8 space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold text-slate-900">知识文档与片段治理</h2>
              <p class="text-xs text-slate-500 mt-1">
                {{ currentRole === 'admin' ? '超管知识审核流 · 多版本快照回滚 · 细粒度分块切片治理' : `负责产品【${currentUserProduct || 'SAAS_CLOUD'}】知识文档提交与切片查阅` }}
              </p>
            </div>
            
            <div class="flex gap-2">
              <button @click="showFaqImportModal = true" class="bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition flex items-center gap-1.5 cursor-pointer">
                <span>💬</span>
                <span>批量录入 FAQ</span>
              </button>
              <button @click="openUploadModal" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition flex items-center gap-1.5 cursor-pointer">
                <span>➕</span>
                <span>上传/录入文档</span>
              </button>
            </div>
          </div>

          <!-- 筛选与视图切换栏 -->
          <div class="bg-white p-4 rounded-2xl border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div class="flex items-center gap-2">
              <button 
                @click="chunkViewTab = 'docs'"
                :class="chunkViewTab === 'docs' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'"
                class="px-3.5 py-1.5 rounded-lg font-semibold transition cursor-pointer"
              >
                📄 知识文档视图 (审核流/版本)
              </button>
              <button 
                @click="chunkViewTab = 'chunks'"
                :class="chunkViewTab === 'chunks' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'"
                class="px-3.5 py-1.5 rounded-lg font-semibold transition cursor-pointer"
              >
                🧩 检索切片视图 (Chunks)
              </button>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <select v-model="filterKbId" @change="onFilterKbChange" class="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium">
                <option value="">全部所属知识库</option>
                <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }} ({{ k.product_code }})</option>
              </select>
              
              <select v-if="chunkViewTab === 'docs'" v-model="filterDocStatus" @change="refreshDocs" class="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium">
                <option value="">全部审核状态</option>
                <option value="ACTIVE">✅ 已生效</option>
                <option value="PENDING_REVIEW">⏳ 待超管审核</option>
                <option value="REJECTED">❌ 已驳回</option>
              </select>

              <select v-if="chunkViewTab === 'docs'" v-model="filterDocType" @change="refreshDocs" class="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5">
                <option value="">全部类型</option>
                <option value="MD">Markdown</option>
                <option value="TXT">TXT纯文本</option>
                <option value="FAQ">FAQ问答库</option>
              </select>

              <select v-if="chunkViewTab === 'chunks'" v-model="filterDocId" @change="onFilterDocChange" class="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium">
                <option value="">全部文档切片</option>
                <option v-for="d in documents" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>

              <input 
                v-model="searchKeyword" 
                @input="handleSearch"
                type="text" 
                placeholder="搜索名称或切片正文..." 
                class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <!-- 视图 A: 文档列表视图 (支持超管审核流、版本回滚、编辑) -->
          <div v-if="chunkViewTab === 'docs'" class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-2xs">
            <table class="w-full text-left text-xs text-slate-700">
              <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px]">
                <tr>
                  <th class="py-3 px-4">文档名称</th>
                  <th class="py-3 px-4">归属知识库</th>
                  <th class="py-3 px-4">审核状态</th>
                  <th class="py-3 px-4">格式</th>
                  <th class="py-3 px-4">优先级</th>
                  <th class="py-3 px-4">版本号</th>
                  <th class="py-3 px-4">提交人</th>
                  <th class="py-3 px-4">更新时间</th>
                  <th class="py-3 px-4 text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="doc in documents" :key="doc.id" class="hover:bg-slate-50 transition">
                  <td class="py-3 px-4 font-semibold text-slate-900 flex items-center gap-2">
                    <span v-if="doc.doc_type === 'MD'">📝</span>
                    <span v-else-if="doc.doc_type === 'FAQ'">💬</span>
                    <span v-else>📄</span>
                    <span class="truncate max-w-xs" :title="doc.name">{{ doc.name }}</span>
                  </td>
                  <td class="py-3 px-4 font-medium text-slate-600">
                    {{ getKbName(doc.kb_id) }}
                  </td>
                  <!-- 审核状态列 -->
                  <td class="py-3 px-4">
                    <span v-if="doc.status === 'ACTIVE'" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      ✅ 已生效
                    </span>
                    <span v-else-if="doc.status === 'PENDING_REVIEW'" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 animate-pulse">
                      ⏳ 待超管审核
                    </span>
                    <span v-else-if="doc.status === 'REJECTED'" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                      ❌ 已驳回
                    </span>
                    <span v-else class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                      {{ doc.status }}
                    </span>
                  </td>
                  <td class="py-3 px-4 font-mono">
                    <span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">{{ doc.doc_type }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="text-amber-500 font-bold">★ {{ doc.priority }}</span>
                  </td>
                  <td class="py-3 px-4 font-mono font-bold text-indigo-600">v{{ doc.version }}</td>
                  <td class="py-3 px-4 text-slate-600">{{ doc.created_by || 'admin' }}</td>
                  <td class="py-3 px-4 text-slate-400 font-mono">{{ (doc.updated_at || '').slice(0, 16).replace('T', ' ') }}</td>
                  <td class="py-3 px-4 text-right space-x-1 whitespace-nowrap">
                    <!-- 超级管理员审核操作 -->
                    <template v-if="currentRole === 'admin' && doc.status === 'PENDING_REVIEW'">
                      <button @click="approveDoc(doc)" class="text-emerald-700 hover:text-emerald-900 font-bold px-2 py-1 bg-emerald-100 hover:bg-emerald-200 rounded-md transition shadow-xs cursor-pointer">
                        ✅ 批准生效
                      </button>
                      <button @click="rejectDoc(doc)" class="text-rose-700 hover:text-rose-900 font-bold px-2 py-1 bg-rose-100 hover:bg-rose-200 rounded-md transition shadow-xs cursor-pointer">
                        ❌ 驳回
                      </button>
                    </template>

                    <!-- 预览按钮 -->
                    <button @click="openPreviewDoc(doc)" class="text-indigo-600 hover:text-indigo-800 font-semibold px-2 py-1 bg-indigo-50 hover:bg-indigo-100 rounded-md transition cursor-pointer">
                      👁️ 预览
                    </button>
                    <!-- 编辑按钮 (客服与超管) -->
                    <button @click="openEditDocModal(doc)" class="text-emerald-700 hover:text-emerald-900 font-semibold px-2 py-1 bg-emerald-50 hover:bg-emerald-100 rounded-md transition cursor-pointer">
                      ✏️ 编辑
                    </button>
                    <!-- 切片直达 -->
                    <button @click="viewDocChunks(doc)" class="text-sky-700 hover:text-sky-900 font-semibold px-2 py-1 bg-sky-50 hover:bg-sky-100 rounded-md transition cursor-pointer">
                      🧩 切片
                    </button>
                    <!-- 版本历史与回滚 -->
                    <button @click="openVersionModal(doc)" class="text-amber-700 hover:text-amber-900 font-semibold px-2 py-1 bg-amber-50 hover:bg-amber-100 rounded-md transition cursor-pointer">
                      🕰️ 历史
                    </button>
                    <!-- 删除文档 (仅超管) -->
                    <button v-if="currentRole === 'admin'" @click="deleteDoc(doc)" class="text-rose-600 hover:text-rose-800 font-semibold px-2 py-1 bg-rose-50 hover:bg-rose-100 rounded-md transition cursor-pointer">
                      🗑️
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="documents.length === 0" class="p-8 text-center text-xs text-slate-400">
              当前知识库下暂无文档
            </div>
          </div>

          <!-- 视图 B: 检索切片视图 (Chunks) -->
          <div v-if="chunkViewTab === 'chunks'" class="space-y-3">
            <div v-for="c in chunkList" :key="c.id" class="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs hover:shadow-sm transition space-y-2">
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  <span class="w-6 h-6 rounded-lg bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-[10px]">#{{ c.chunk_index }}</span>
                  <span class="font-bold text-slate-900">{{ c.doc_name }}</span>
                  <span class="text-[11px] text-slate-500 font-mono">({{ c.heading_path || '文档正文' }})</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-amber-500 font-semibold text-[11px]">★ 优先级: {{ c.priority }}</span>
                  <span class="text-[10px] font-mono text-slate-400">ID: {{ c.id.slice(0, 8) }}</span>
                </div>
              </div>
              <p class="text-xs text-slate-700 leading-relaxed font-mono whitespace-pre-wrap bg-slate-50 p-3 rounded-xl border border-slate-100">
                {{ c.content }}
              </p>
            </div>
            <div v-if="chunkList.length === 0" class="bg-white border border-slate-200 rounded-2xl p-8 text-center text-xs text-slate-400">
              暂无匹配的切片数据
            </div>
        </section>

        <!-- ================= 模块 3: 知识库管理 (仅 超级管理员 可见) ================= -->
        <section v-if="activeMenu === 'kb' && hasMenuPermission('kb')" class="flex-1 overflow-y-auto p-8 space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold text-slate-900">知识库治理中心</h2>
              <p class="text-xs text-slate-500 mt-1">创建多产品知识库、调优 BM25/向量召回与重排阈值参数</p>
            </div>
            <button @click="showCreateKBDocModal = true" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition flex items-center gap-1.5 cursor-pointer">
              <span>➕</span>
              <span>创建产品知识库</span>
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="kb in kbs" :key="kb.id" class="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs hover:shadow-md transition space-y-4">
              <div class="flex items-start justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <h3 class="font-bold text-slate-900 text-sm">{{ kb.name }}</h3>
                    <!-- Switch 切换启用/停用 -->
                    <button 
                      @click="toggleKBStatus(kb)"
                      :class="kb.status === 'ACTIVE' ? 'bg-indigo-600' : 'bg-slate-300'"
                      class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out"
                    >
                      <span :class="kb.status === 'ACTIVE' ? 'translate-x-4 bg-white' : 'translate-x-0 bg-white'" class="pointer-events-none inline-block h-4 w-4 transform rounded-full shadow-sm ring-0 transition duration-200 ease-in-out"></span>
                    </button>
                  </div>
                  <span class="text-[10px] font-mono text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded-md inline-block mt-1">
                    产品编码: {{ kb.product_code }}
                  </span>
                </div>
                <button @click="openEditKBModal(kb)" class="text-slate-400 hover:text-indigo-600 text-xs font-medium cursor-pointer">
                  ✏️ 编辑
                </button>
              </div>

              <p class="text-xs text-slate-500 line-clamp-2">{{ kb.description || '暂无描述信息' }}</p>

              <div class="grid grid-cols-2 gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-[11px]">
                <div>
                  <span class="text-slate-400">生效文档:</span>
                  <span class="font-bold text-slate-700 ml-1">{{ kb.doc_count || 0 }} 篇</span>
                </div>
                <div>
                  <span class="text-slate-400">向量切片:</span>
                  <span class="font-bold text-slate-700 ml-1">{{ kb.chunk_count || 0 }} 个</span>
                </div>
              </div>

              <div class="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                <button @click="openConfigModal(kb)" class="text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer">
                  ⚙️ 检索与重排阈值配置
                </button>
                <button @click="confirmDeleteKB(kb)" class="text-rose-600 hover:text-rose-800 font-semibold cursor-pointer">
                  🗑️ 级联删除
                </button>
              </div>
            </div>
        </section>

        <!-- ================= 模块 4: BadCase 闭环治理工作台 (超管与运营可见) ================= -->
        <section v-if="activeMenu === 'badcases' && hasMenuPermission('badcases')" class="flex-1 overflow-y-auto p-6 space-y-6">
          
          <!-- 顶部标题与快捷操作 -->
          <div class="flex items-center justify-between">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">🚨</span>
                <h2 class="text-xl font-bold text-slate-900">BadCase 闭环治理工作台</h2>
                <span class="text-[10px] bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-bold">
                  {{ currentRole === 'admin' ? '全域治理' : `运营专属 (${assignedKbName})` }}
                </span>
              </div>
              <p class="text-xs text-slate-500 mt-1">
                多源差评采集 ➔ 稠密向量凝聚聚类 ➔ 场景智能预判 ➔ 一键采纳知识草稿 ➔ 效果回流回归闭环
              </p>
            </div>
            
            <div class="flex gap-2">
              <button 
                @click="openAnalyticsDashboard" 
                class="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 shadow-2xs cursor-pointer"
              >
                <span>📊</span>
                <span>转化全景看板</span>
              </button>
              <button 
                @click="triggerClustering" 
                :disabled="isClustering"
                class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition flex items-center gap-1.5 shadow-md shadow-indigo-500/20 disabled:opacity-50 cursor-pointer"
              >
                <span v-if="isClustering" class="animate-spin">⏳</span>
                <span v-else>⚡</span>
                <span>{{ isClustering ? '正在凝聚聚类中...' : '一键语义聚类' }}</span>
              </button>
              <button 
                @click="fetchBadCasesAndClusters" 
                class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-xl transition cursor-pointer"
              >
                <span>🔄 刷新</span>
              </button>
            </div>
          </div>

          <!-- 4 项宏观核心指标卡片 -->
          <div class="grid grid-cols-4 gap-4">
            <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-1">
              <div class="flex items-center justify-between text-slate-400 text-xs">
                <span>累计采集 BadCase</span>
                <span class="text-base">📥</span>
              </div>
              <div class="text-2xl font-black text-slate-900 font-mono">{{ dashboardStats.total_cases_collected || 0 }}</div>
              <div class="text-[10px] text-slate-400 flex items-center gap-1.5">
                <span>用户差评: {{ dashboardStats.case_types?.user_feedback || 0 }}</span>
                <span>·</span>
                <span>低置信: {{ dashboardStats.case_types?.low_confidence || 0 }}</span>
                <span>·</span>
                <span>坐席标错: {{ dashboardStats.case_types?.agent_label || 0 }}</span>
              </div>
            </div>

            <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-1">
              <div class="flex items-center justify-between text-slate-400 text-xs">
                <span>高频问题簇总数</span>
                <span class="text-base">🧩</span>
              </div>
              <div class="text-2xl font-black text-indigo-600 font-mono">{{ dashboardStats.total_clusters || 0 }}</div>
              <div class="text-[10px] text-slate-400">稠密向量距离自动归拢聚类</div>
            </div>

            <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-1">
              <div class="flex items-center justify-between text-slate-400 text-xs">
                <span>待治理问题簇</span>
                <span class="text-base">⏳</span>
              </div>
              <div class="text-2xl font-black text-amber-500 font-mono">{{ dashboardStats.pending_clusters || 0 }}</div>
              <div class="text-[10px] text-amber-600 font-medium">亟待运营采纳或补充知识库</div>
            </div>

            <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-1">
              <div class="flex items-center justify-between text-slate-400 text-xs">
                <span>闭环回归通过率</span>
                <span class="text-base">🎯</span>
              </div>
              <div class="text-2xl font-black text-emerald-600 font-mono">{{ dashboardStats.average_pass_rate || 0 }}%</div>
              <div class="text-[10px] text-emerald-600 font-medium">真实历史问句回归测试达标率</div>
            </div>
          </div>

          <!-- 子 Tab 导航栏：问题簇 / 全量池与长尾 / 判定阈值配置 -->
          <div class="flex items-center gap-2 border-b border-slate-200 pb-3">
            <button 
              @click="badcaseActiveTab = 'clusters'" 
              :class="badcaseActiveTab === 'clusters' ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'"
              class="px-4 py-2 rounded-xl text-xs transition cursor-pointer flex items-center gap-1.5"
            >
              <span>🔥 高频聚类问题簇治理</span>
              <span class="text-[10px] opacity-80 font-mono">({{ filteredClusters.length }})</span>
            </button>
            <button 
              @click="badcaseActiveTab = 'all_cases'; fetchAllBadCasesList()" 
              :class="badcaseActiveTab === 'all_cases' ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'"
              class="px-4 py-2 rounded-xl text-xs transition cursor-pointer flex items-center gap-1.5"
            >
              <span>📋 全量 BadCase 池与长尾处理</span>
              <span class="text-[10px] opacity-80 font-mono">({{ allBadCasesTotal }})</span>
            </button>
            <button 
              @click="badcaseActiveTab = 'thresholds'; fetchThresholdConfigs()" 
              :class="badcaseActiveTab === 'thresholds' ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'"
              class="px-4 py-2 rounded-xl text-xs transition cursor-pointer flex items-center gap-1.5"
            >
              <span>⚙️ 判定阈值配置与审计日志</span>
            </button>
          </div>

          <!-- Tab 1: 高频聚类问题簇治理 -->
          <div v-show="badcaseActiveTab === 'clusters'" class="space-y-4">
            <!-- 知识库与状态筛选工具栏 -->
            <div class="bg-white p-4 rounded-2xl border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-slate-600">归属知识库:</span>
              <!-- 运营专员锁定单知识库显示，不可越权 -->
              <div v-if="currentRole === 'operator'" class="bg-orange-50 border border-orange-200 text-orange-800 px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5">
                <span>🔒</span>
                <span>{{ assignedKbName }} (当前运营组权限绑定)</span>
              </div>
              <!-- 超级管理员支持自由切换全域知识库 -->
              <select v-else v-model="filterBadCaseKbId" @change="fetchBadCasesAndClusters" class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium">
                <option value="">全部知识库</option>
                <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }} ({{ k.product_code }})</option>
              </select>
            </div>

            <div class="flex items-center gap-2">
              <select v-model="filterBadCaseStatus" @change="fetchBadCasesAndClusters" class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium">
                <option value="">全部治理状态</option>
                <option value="PENDING">⏳ 待处理 (PENDING)</option>
                <option value="ADOPTED">✅ 已采纳/已解决 (ADOPTED)</option>
                <option value="REJECTED">🚫 已驳回 (REJECTED)</option>
              </select>

              <select v-model="filterBadCaseScene" class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium">
                <option value="">全部智能推荐场景</option>
                <option value="ADD_SIMILAR_QUERY">场景 A: 追加相似问</option>
                <option value="NEW_FAQ">场景 B: 新建独立 FAQ</option>
                <option value="REVISE_DOC">场景 C: 修订长文本知识</option>
              </select>

              <input 
                v-model="badCaseSearch" 
                type="text" 
                placeholder="搜索问题簇或关键词..." 
                class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-52"
              />
            </div>
          </div>

          <!-- 双栏主体：左侧问题簇列表，右侧治理工作台详情 -->
          <div class="grid grid-cols-12 gap-6 min-h-[560px]">
            
            <!-- 左侧：聚类簇列表 (热度降序排列) -->
            <div class="col-span-5 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col shadow-2xs">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <div class="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <span>🔥 高频聚类问题簇</span>
                  <span class="text-[10px] bg-slate-100 px-2 py-0.5 rounded-full text-slate-500 font-mono">{{ filteredClusters.length }} 个</span>
                </div>
                <span class="text-[10px] text-slate-400">点击选中展开治理</span>
              </div>

              <!-- 簇列表滚动区 -->
              <div class="flex-1 overflow-y-auto space-y-2.5 mt-3 pr-1">
                <div v-if="filteredClusters.length === 0" class="text-center py-16 text-slate-400 text-xs">
                  暂无匹配的问题簇，可点击右上角【一键语义聚类】生成新簇
                </div>

                <div 
                  v-for="c in filteredClusters" 
                  :key="c.id"
                  @click="selectCluster(c)"
                  class="p-3.5 rounded-xl border transition cursor-pointer space-y-2 relative"
                  :class="selectedCluster?.id === c.id ? 'border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-500/20' : 'border-slate-200 hover:border-indigo-200 bg-slate-50/50 hover:bg-slate-50'"
                >
                  <!-- 顶部：代表提问与热度 -->
                  <div class="flex items-start justify-between gap-2">
                    <p class="font-bold text-xs text-slate-900 leading-snug line-clamp-2">
                      {{ c.cluster_name || c.representative_query }}
                    </p>
                    <span class="flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full font-mono shadow-xs"
                          :class="c.case_count >= 3 ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-amber-100 text-amber-700 border border-amber-200'">
                      🔥 {{ c.case_count }}次进线
                    </span>
                  </div>

                  <!-- 根因与场景状态标签 -->
                  <div class="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <!-- 7 大根因标签 -->
                    <span v-if="c.root_cause_name" class="bg-indigo-100 text-indigo-800 border border-indigo-200 px-2 py-0.5 rounded-md font-bold">
                      🎯 {{ c.root_cause_name }}
                    </span>
                    <!-- 场景徽章 -->
                    <span v-if="c.recommended_action === 'ADD_SIMILAR_QUERY'" class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-md font-semibold">
                      💡 场景A: 追加相似问
                    </span>
                    <span v-else-if="c.recommended_action === 'NEW_FAQ'" class="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-md font-semibold">
                      ✨ 场景B: 新建FAQ
                    </span>
                    <span v-else-if="c.recommended_action === 'REVISE_DOC'" class="bg-amber-100 text-amber-700 px-2 py-0.5 rounded-md font-semibold">
                      📝 场景C: 修订文档
                    </span>

                    <!-- 治理状态徽章 -->
                    <span v-if="c.status === 'PENDING'" class="bg-amber-50 text-amber-600 border border-amber-200 px-1.5 py-0.5 rounded-md">
                      ⏳ 待处理
                    </span>
                    <span v-else-if="c.status === 'ADOPTED'" class="bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded-md font-bold">
                      ✅ 已采纳
                    </span>
                    <span v-else-if="c.status === 'REJECTED'" class="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-md">
                      🚫 已驳回
                    </span>

                    <span class="ml-auto text-slate-400 font-mono text-[9px]">
                      {{ (c.created_at || '').slice(5, 16).replace('T', ' ') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧：工作台详情与采纳/回流操作 -->
            <div class="col-span-7 bg-white border border-slate-200 rounded-2xl p-5 flex flex-col shadow-2xs">
              <div v-if="!selectedCluster" class="flex-1 flex flex-col items-center justify-center text-slate-400 text-xs space-y-2">
                <span class="text-4xl">👈</span>
                <p class="font-medium">请从左侧选择一个问题簇开展闭环治理</p>
                <p class="text-[11px] text-slate-400">支持查看 AI 智能诊断、用户多形态口语提问、一键生成知识草稿及回归测试</p>
              </div>

              <div v-else class="flex-1 flex flex-col space-y-4">
                
                <!-- 头部：簇标题、状态与动作按钮 -->
                <div class="flex items-start justify-between pb-3 border-b border-slate-100 gap-3">
                  <div>
                    <div class="flex items-center gap-2">
                      <h3 class="text-sm font-bold text-slate-900 leading-tight">
                        {{ selectedCluster.cluster_name || selectedCluster.representative_query }}
                      </h3>
                      <span class="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold"
                            :class="selectedCluster.status === 'ADOPTED' ? 'bg-emerald-100 text-emerald-800' : (selectedCluster.status === 'REJECTED' ? 'bg-slate-100 text-slate-600' : 'bg-amber-100 text-amber-800')">
                        {{ selectedCluster.status === 'ADOPTED' ? '已采纳生效' : (selectedCluster.status === 'REJECTED' ? '已驳回' : '待处理') }}
                      </span>
                    </div>
                    <p class="text-[11px] text-slate-400 mt-1 flex items-center gap-2">
                      <span>频次: {{ selectedCluster.case_count }} 次</span>
                      <span>·</span>
                      <span>知识库: {{ getKbNameById(selectedCluster.kb_id) }}</span>
                    </p>
                  </div>

                  <!-- 顶部快捷操作 -->
                  <div class="flex gap-1.5 flex-shrink-0">
                    <button 
                      @click="openAdoptModal(selectedCluster)"
                      class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3 py-1.5 rounded-xl transition flex items-center gap-1 shadow-xs cursor-pointer"
                    >
                      <span>✨ 一键采纳</span>
                    </button>
                    <button 
                      v-if="selectedCluster.target_knowledge_id"
                      @click="openReviseDocModal(selectedCluster.target_knowledge_id, selectedCluster.target_knowledge_title || '关联文档', null, selectedCluster.id)"
                      class="bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 text-xs font-semibold px-2.5 py-1.5 rounded-xl transition cursor-pointer flex items-center gap-1"
                    >
                      <span>📝</span>
                      <span>修订原文档</span>
                    </button>
                    <button 
                      @click="openLinkModal(selectedCluster)"
                      class="bg-sky-50 hover:bg-sky-100 border border-sky-200 text-sky-800 text-xs font-semibold px-2.5 py-1.5 rounded-xl transition cursor-pointer"
                    >
                      <span>🔗 关联知识</span>
                    </button>
                    <button 
                      @click="openRejectModal(selectedCluster)"
                      class="bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 text-xs px-2.5 py-1.5 rounded-xl transition cursor-pointer"
                    >
                      <span>🚫 驳回</span>
                    </button>
                    <button 
                      @click="runRegressionValidation(selectedCluster)"
                      :disabled="isValidating"
                      class="bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold px-3 py-1.5 rounded-xl transition flex items-center gap-1 cursor-pointer disabled:opacity-50"
                    >
                      <span v-if="isValidating" class="animate-spin">⏳</span>
                      <span v-else>🧪</span>
                      <span>回流验证</span>
                    </button>
                  </div>
                </div>

                <div class="flex-1 overflow-y-auto space-y-4 pr-1 text-xs">
                  
                  <!-- 卡片 1: AI 智能预判断与推荐治理动作 -->
                  <div class="bg-gradient-to-r from-indigo-50/70 via-sky-50/50 to-white p-4 rounded-xl border border-indigo-100 space-y-2">
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-indigo-950 flex items-center gap-1.5">
                        <span>🤖 智能诊断决策与治理建议</span>
                      </span>
                      <span class="text-[10px] bg-white px-2 py-0.5 rounded-md border border-indigo-200 text-indigo-700 font-mono font-bold">
                        置信度: {{ ((selectedCluster.confidence || 0.85) * 100).toFixed(0) }}%
                      </span>
                    </div>

                    <div class="text-xs text-slate-700 space-y-2 leading-relaxed">
                      <div v-if="selectedCluster.root_cause_name" class="bg-white p-3 rounded-xl border border-indigo-200 space-y-1">
                        <div class="flex items-center justify-between">
                          <span class="font-bold text-slate-800 text-xs">【簇整体根因】: <span class="text-indigo-700 font-extrabold">{{ selectedCluster.root_cause_name }}</span></span>
                          <span class="text-[10px] bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded font-mono font-bold">加权表决裁定</span>
                        </div>
                        <p class="text-[11px] text-slate-600"><strong>官方定义:</strong> {{ selectedCluster.root_cause_description || '知识库规则缺失或召回偏离' }}</p>
                        <div v-if="selectedCluster.root_cause_distribution" class="text-[10px] text-slate-400 flex items-center gap-2 pt-0.5 font-mono">
                          <span>簇内根因分布:</span>
                          <span v-for="(cnt, rk) in selectedCluster.root_cause_distribution" :key="rk" class="bg-slate-100 px-1.5 py-0.2 rounded text-slate-600">
                            {{ rk }}: {{ cnt }}笔
                          </span>
                        </div>
                      </div>

                      <p><strong>推荐动作:</strong> 
                        <span class="font-bold text-indigo-700">
                          {{ getActionDisplay(selectedCluster.recommended_action) }}
                        </span>
                      </p>
                      <p><strong>诊断依据:</strong> {{ selectedCluster.recommended_reason || '根据近期多位用户针对同类问题的差评反馈与检索切片置信度聚类生成' }}</p>
                      <p v-if="selectedCluster.suggested_standard_query">
                        <strong>建议标准问题:</strong> <span class="text-indigo-900 font-semibold">{{ selectedCluster.suggested_standard_query }}</span>
                      </p>
                    </div>
                  </div>

                  <!-- 卡片 2: 用户口语化提问聚合池 (Sample Queries) -->
                  <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-slate-800 text-xs flex items-center gap-1">
                        <span>🗣️ 聚类聚集的用户真实口语问法 ({{ (selectedCluster.sample_queries || []).length }} 种表达)</span>
                      </span>
                      <span class="text-[10px] text-slate-400">已自动完成向量归一化去重</span>
                    </div>

                    <div class="flex flex-wrap gap-1.5 pt-1">
                      <span 
                        v-for="(sq, sidx) in (selectedCluster.sample_queries || [])" 
                        :key="sidx"
                        class="bg-white border border-slate-200 text-slate-700 px-2.5 py-1 rounded-lg text-xs font-mono shadow-2xs hover:border-indigo-300 transition"
                      >
                        {{ sq }}
                      </span>
                    </div>
                  </div>

                  <!-- 卡片 3: 原始 BadCase 溯源明细 (展示会话上下文与差评详情) -->
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-slate-800 text-xs">
                        📋 溯源明细与进线记录 (共 {{ clusterCases.length }} 笔)
                      </span>
                      <button @click="fetchClusterCases(selectedCluster.id)" class="text-indigo-600 text-[10px] hover:underline cursor-pointer">
                        刷新记录
                      </button>
                    </div>

                    <div class="space-y-2">
                      <div 
                        v-for="item in clusterCases" 
                        :key="item.id"
                        class="p-3 bg-white border border-slate-200 rounded-xl space-y-2 text-xs"
                      >
                        <div class="flex items-center justify-between text-[11px]">
                          <span class="font-bold flex items-center gap-1.5"
                                :class="item.case_type === 'USER_FEEDBACK' ? 'text-rose-600' : (item.case_type === 'AGENT_LABEL' ? 'text-amber-600' : 'text-sky-600')">
                            <span>{{ item.case_type === 'USER_FEEDBACK' ? '👎 用户差评' : (item.case_type === 'AGENT_LABEL' ? '🏷️ 坐席标注' : '🤖 隐式未命中') }}</span>
                            <span v-if="item.user_feedback_comment" class="bg-rose-50 text-rose-700 px-1.5 py-0.2 rounded font-normal text-[10px]">
                              反馈说明: {{ item.user_feedback_comment }}
                            </span>
                            <span v-if="item.agent_label_category" class="bg-amber-50 text-amber-700 px-1.5 py-0.2 rounded font-normal text-[10px]">
                              错误类型: {{ item.agent_label_category }}
                            </span>
                          </span>
                          <span class="text-slate-400 font-mono text-[10px]">{{ (item.created_at || '').slice(0, 16).replace('T', ' ') }}</span>
                        </div>

                        <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 space-y-1.5">
                          <p class="font-semibold text-slate-900"><strong>用户提问:</strong> {{ item.user_query }}</p>
                          <p class="text-slate-600 line-clamp-2"><strong>AI回答:</strong> {{ item.ai_raw_response }}</p>
                          
                          <!-- 命中切片来源胶囊 -->
                          <div class="flex items-center gap-2 pt-1 border-t border-slate-200/60">
                            <span class="text-[10px] font-semibold text-slate-500">命中知识:</span>
                            <span v-if="item.recall_sources && item.recall_sources.length > 0" class="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded text-[10px] font-medium">
                              <span>📚</span>
                              <span>《{{ item.recall_sources[0].doc_name || '对应知识文档' }}》</span>
                              <span v-if="item.recall_sources[0].heading" class="text-indigo-400">/ {{ item.recall_sources[0].heading }}</span>
                            </span>
                            <span v-else class="inline-flex items-center gap-1 bg-rose-50 text-rose-600 border border-rose-200 px-2 py-0.5 rounded text-[10px] font-medium">
                              <span>⚠️</span>
                              <span>纯业务盲区 (未召回任何有效切片)</span>
                            </span>
                            <span class="ml-auto text-[10px] text-slate-400 font-mono">置信得分: {{ ((item.confidence_score || 0) * 100).toFixed(0) }}%</span>
                            <button 
                              v-if="item.recall_sources && item.recall_sources[0] && item.recall_sources[0].doc_id"
                              @click="openReviseDocModal(item.recall_sources[0].doc_id, item.recall_sources[0].doc_name, item.id, selectedCluster?.id)"
                              class="text-[10px] text-amber-700 hover:text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-2 py-0.5 rounded transition cursor-pointer"
                            >
                              📝 修订此文档
                            </button>
                          </div>

                          <!-- 单条客观测根因定位 -->
                          <div v-if="item.root_cause_name" class="flex items-center gap-1.5 text-[10px] bg-white p-1.5 rounded border border-slate-200/80">
                            <span class="font-bold text-slate-700">根因初诊:</span>
                            <span class="bg-indigo-100 text-indigo-800 font-bold px-1.5 py-0.2 rounded">{{ item.root_cause_name }}</span>
                            <span class="text-slate-500 font-normal truncate">{{ item.root_cause_reason }}</span>
                          </div>
                        </div>

                        <!-- 展开查看前置上下文 -->
                        <div v-if="item.chat_context && item.chat_context.length > 0" class="pt-1">
                          <details class="cursor-pointer">
                            <summary class="text-[10px] text-indigo-600 font-semibold hover:underline">展开查阅当时前置 {{ item.chat_context.length }} 轮对话上下文</summary>
                            <div class="mt-2 p-2 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5 text-[11px] font-mono">
                              <div v-for="(ctx, cidx) in item.chat_context" :key="cidx" :class="ctx.role === 'user' ? 'text-indigo-900 font-semibold' : 'text-slate-700'">
                                <span>{{ ctx.role === 'user' ? '👤 客户: ' : '🤖 AI: ' }}</span>
                                <span>{{ ctx.content }}</span>
                              </div>
                            </div>
                          </details>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            </div>

          </div>
                  </div> <!-- 关闭 Tab 1 -->

          <!-- ================= Tab 2: 全量 BadCase 池与长尾治理 ================= -->
          <div v-show="badcaseActiveTab === 'all_cases'" class="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-2xs">
            <!-- 顶部多维筛选工具栏与批量建簇按钮 -->
            <div class="flex flex-wrap items-center justify-between gap-3 text-xs pb-3 border-b border-slate-100">
              <div class="flex flex-wrap items-center gap-2">
                <select v-model="filterCaseStatus" @change="fetchAllBadCasesList" class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium">
                  <option value="">全部处理状态</option>
                  <option value="PENDING">⏳ 待处理 (PENDING)</option>
                  <option value="CLUSTERED">🧩 已入簇 (CLUSTERED)</option>
                  <option value="ADOPTED">✅ 已采纳 (ADOPTED)</option>
                  <option value="REJECTED">🚫 已驳回 (REJECTED)</option>
                </select>

                <select v-model="filterClusterStatus" @change="fetchAllBadCasesList" class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium">
                  <option value="all">全部归属形态</option>
                  <option value="unclustered">长尾孤岛 (未入簇)</option>
                  <option value="clustered">已聚合进簇</option>
                </select>

                <select v-model="filterRootCause" @change="fetchAllBadCasesList" class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium">
                  <option value="">全部根因类型</option>
                  <option value="RC_KNOWLEDGE_MISSING">知识缺失</option>
                  <option value="RC_RECALL_INSUFFICIENT">召回不足</option>
                  <option value="RC_KNOWLEDGE_ERROR">知识错误 / 过时</option>
                  <option value="RC_MATCH_CONFUSION">匹配混淆</option>
                  <option value="RC_CONTEXT_MISSING">上下文缺失</option>
                  <option value="RC_QUERY_AMBIGUOUS">用户问题模糊</option>
                  <option value="RC_INVALID_CASE">无效 case</option>
                </select>

                <input 
                  v-model="caseSearchKeyword" 
                  @keyup.enter="fetchAllBadCasesList"
                  type="text" 
                  placeholder="回车搜索提问内容..." 
                  class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-48"
                />
                <button @click="fetchAllBadCasesList" class="bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg text-slate-700 font-semibold cursor-pointer">
                  🔍 查询
                </button>
              </div>

              <!-- 批量手动合并建簇按钮 -->
              <div class="flex items-center gap-2">
                <span class="text-slate-400 text-xs">已勾选 {{ selectedCaseIds.length }} 项</span>
                <button 
                  @click="openManualClusterModal"
                  :disabled="selectedCaseIds.length === 0"
                  class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3.5 py-1.5 rounded-xl transition cursor-pointer disabled:opacity-40 flex items-center gap-1 shadow-xs"
                >
                  <span>🧩 手动合并建簇</span>
                </button>
              </div>
            </div>

            <!-- 全量 BadCase 表格列表 -->
            <div class="overflow-x-auto text-xs">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-slate-50/70 border-b border-slate-200 text-slate-500">
                    <th class="p-3 w-10 text-center">
                      <input type="checkbox" @change="toggleSelectAllCases" class="rounded cursor-pointer" />
                    </th>
                    <th class="p-3 w-28">类型 / 状态</th>
                    <th class="p-3">用户真实提问与回答</th>
                    <th class="p-3 w-36">根因定位初诊</th>
                    <th class="p-3 w-48">命中切片知识</th>
                    <th class="p-3 w-24">归属形态</th>
                    <th class="p-3 w-36 text-center">独立治理操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr v-if="allBadCases.length === 0">
                    <td colspan="7" class="text-center py-12 text-slate-400">暂无符合条件的 BadCase 记录</td>
                  </tr>
                  <tr v-for="c in allBadCases" :key="c.id" class="hover:bg-slate-50/60 transition">
                    <td class="p-3 text-center">
                      <input type="checkbox" :checked="selectedCaseIds.includes(c.id)" @change="toggleSelectCase(c.id)" class="rounded cursor-pointer" />
                    </td>
                    <td class="p-3 space-y-1">
                      <span class="font-bold text-[10px] px-2 py-0.5 rounded-full inline-block"
                            :class="c.case_type === 'USER_FEEDBACK' ? 'bg-rose-100 text-rose-700' : (c.case_type === 'AGENT_LABEL' ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700')">
                        {{ c.case_type === 'USER_FEEDBACK' ? '👎 用户差评' : (c.case_type === 'AGENT_LABEL' ? '🏷️ 坐席标注' : '🤖 隐式未命中') }}
                      </span>
                      <div class="text-[10px] text-slate-400 font-mono">{{ (c.created_at || '').slice(5, 16).replace('T', ' ') }}</div>
                    </td>
                    <td class="p-3 space-y-1 max-w-md">
                      <p class="font-bold text-slate-900 leading-snug">{{ c.user_query }}</p>
                      <p class="text-slate-500 line-clamp-1 text-[11px]">{{ c.ai_raw_response }}</p>
                    </td>
                    <td class="p-3">
                      <span v-if="c.root_cause_name" class="bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded font-bold text-[10px]">
                        {{ c.root_cause_name }}
                      </span>
                      <span v-else class="text-slate-400 text-[10px]">待诊断</span>
                    </td>
                    <td class="p-3">
                      <div v-if="c.recall_sources && c.recall_sources.length > 0">
                        <span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-medium block truncate max-w-[180px]">
                          📚 {{ c.recall_sources[0].doc_name }}
                        </span>
                      </div>
                      <div v-else>
                        <span class="bg-rose-50 text-rose-600 px-1.5 py-0.5 rounded text-[10px]">⚠️ 纯盲区</span>
                      </div>
                    </td>
                    <td class="p-3">
                      <span class="text-[10px] px-2 py-0.5 rounded-md font-mono"
                            :class="c.cluster_id ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'">
                        {{ c.cluster_id ? '已归簇' : '长尾单点' }}
                      </span>
                    </td>
                    <td class="p-3 text-center space-x-1 whitespace-nowrap">
                      <button 
                        @click="openSingleAdoptModal(c)" 
                        class="text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2 py-1 rounded text-[10px] font-semibold cursor-pointer"
                      >
                        ✨ 采纳
                      </button>
                      <button 
                        v-if="c.recall_sources && c.recall_sources[0] && c.recall_sources[0].doc_id"
                        @click="openReviseDocModal(c.recall_sources[0].doc_id, c.recall_sources[0].doc_name, c.id, null)" 
                        class="text-amber-700 hover:text-amber-900 bg-amber-50 hover:bg-amber-100 px-2 py-1 rounded text-[10px] font-semibold cursor-pointer"
                      >
                        📝 修订
                      </button>
                      <button 
                        @click="openSingleRejectModal(c)" 
                        class="text-slate-500 hover:text-rose-600 bg-slate-100 hover:bg-rose-50 px-2 py-1 rounded text-[10px] cursor-pointer"
                      >
                        🚫 驳回
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页控制器 -->
            <div class="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500">
              <div>共 {{ allBadCasesTotal }} 笔 BadCase 记录</div>
              <div class="flex items-center gap-1.5">
                <button 
                  @click="allBadCasesPage--; fetchAllBadCasesList()" 
                  :disabled="allBadCasesPage <= 1" 
                  class="px-2.5 py-1 bg-slate-100 rounded hover:bg-slate-200 disabled:opacity-40 cursor-pointer"
                >上一页</button>
                <span class="px-2 font-mono">第 {{ allBadCasesPage }} 页</span>
                <button 
                  @click="allBadCasesPage++; fetchAllBadCasesList()" 
                  :disabled="allBadCasesPage * allBadCasesPageSize >= allBadCasesTotal" 
                  class="px-2.5 py-1 bg-slate-100 rounded hover:bg-slate-200 disabled:opacity-40 cursor-pointer"
                >下一页</button>
              </div>
            </div>
          </div>

          <!-- ================= Tab 3: 判定阈值配置与审计日志 ================= -->
          <div v-show="badcaseActiveTab === 'thresholds'" class="grid grid-cols-12 gap-6">
            <!-- 左侧：参数配置面板 -->
            <div class="col-span-6 bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-2xs">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 class="text-sm font-bold text-slate-800">按知识库维度的规则判定阈值配置</h3>
                  <p class="text-[11px] text-slate-400 mt-0.5">支持针对不同产品线（SaaS / 电商）独立调优检索断言与多轮边界</p>
                </div>
                <button 
                  @click="submitThresholdConfig" 
                  :disabled="isSavingThreshold"
                  class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition cursor-pointer shadow-xs disabled:opacity-50"
                >
                  {{ isSavingThreshold ? '保存中...' : '💾 保存配置' }}
                </button>
              </div>

              <div class="space-y-3.5 text-xs">
                <div>
                  <label class="block font-semibold text-slate-700 mb-1">目标知识库</label>
                  <select v-model="selectedThresholdKbId" @change="onThresholdKbChange" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
                    <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }} ({{ k.product_code }})</option>
                  </select>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block font-semibold text-slate-700 mb-1">无答案底线阈值 (threshold_low)</label>
                    <input v-model.number="thresholdForm.threshold_low" type="number" step="0.05" min="0" max="1" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
                    <span class="text-[10px] text-slate-400 mt-0.5 block">低于此分值判定为【知识缺失】</span>
                  </div>
                  <div>
                    <label class="block font-semibold text-slate-700 mb-1">强命中高分阈值 (threshold_high)</label>
                    <input v-model.number="thresholdForm.threshold_high" type="number" step="0.05" min="0" max="1" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
                    <span class="text-[10px] text-slate-400 mt-0.5 block">达标仍差评判定为【知识错误/过时】</span>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block font-semibold text-slate-700 mb-1">指代短句字数上限 (short_query_len)</label>
                    <input v-model.number="thresholdForm.short_query_len" type="number" min="2" max="20" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
                    <span class="text-[10px] text-slate-400 mt-0.5 block">含代词且字数短判定为【上下文缺失】</span>
                  </div>
                  <div>
                    <label class="block font-semibold text-slate-700 mb-1">多轮滑动记忆轮数 (context_window_rounds)</label>
                    <input v-model.number="thresholdForm.context_window_rounds" type="number" min="1" max="10" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
                    <span class="text-[10px] text-slate-400 mt-0.5 block">以用户输入为计数锚点回溯</span>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block font-semibold text-slate-700 mb-1">候选切片监控起始位</label>
                    <input v-model.number="thresholdForm.candidate_rank_start" type="number" min="1" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
                  </div>
                  <div>
                    <label class="block font-semibold text-slate-700 mb-1">候选切片监控结束位</label>
                    <input v-model.number="thresholdForm.candidate_rank_end" type="number" min="1" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧：审计变更日志表格 -->
            <div class="col-span-6 bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-2xs">
              <div class="pb-3 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h3 class="text-sm font-bold text-slate-800">阈值变更审计日志</h3>
                  <p class="text-[11px] text-slate-400 mt-0.5">调优全生命周期可追溯、防误触回滚依据</p>
                </div>
                <button @click="fetchThresholdLogs" class="text-indigo-600 text-xs hover:underline cursor-pointer">刷新日志</button>
              </div>

              <div class="overflow-y-auto max-h-[480px] space-y-2.5 text-xs">
                <div v-if="thresholdAuditLogs.length === 0" class="text-center py-12 text-slate-400">暂无阈值变更日志记录</div>
                <div v-for="log in thresholdAuditLogs" :key="log.id" class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <div class="flex items-center justify-between text-[11px]">
                    <span class="font-bold text-slate-800">操作人: {{ log.operator }}</span>
                    <span class="text-slate-400 font-mono">{{ (log.changed_at || '').slice(0, 16).replace('T', ' ') }}</span>
                  </div>
                  <div class="text-[11px] text-slate-600 font-mono">
                    <span>新阈值: low={{ log.new_values?.threshold_low }}, high={{ log.new_values?.threshold_high }}, rounds={{ log.new_values?.context_window_rounds }}</span>
                  </div>
                </div>
              </div>
            </div>
        </section>

      </main>
    </div>

    <!-- ================= 模态弹窗与抽屉 ================= -->

    <!-- 弹窗: 修订长文本知识库草稿 (场景 C 闭环) -->
    <div v-if="showReviseDocModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-800">📝 修订知识文档正文草稿</h3>
            <p class="text-[11px] text-slate-400 mt-0.5">针对《{{ reviseDocForm.doc_name }}》发起版本修订，保存后自动进入超管审核流</p>
          </div>
          <button @click="showReviseDocModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>
        <div class="space-y-3.5 text-xs flex-1 overflow-y-auto pr-1">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">修订原因 / 变更说明</label>
            <input v-model="reviseDocForm.change_summary" type="text" placeholder="例如：补充生鲜开封不退例外免责细则" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">修订后文档完整内容</label>
            <textarea v-model="reviseDocForm.new_content" rows="12" placeholder="在此编辑或增补条款正文..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-mono text-xs focus:ring-1 focus:ring-indigo-500"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showReviseDocModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitReviseDoc" :disabled="isSubmittingRevise" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md cursor-pointer disabled:opacity-50">
            {{ isSubmittingRevise ? '正在提交草稿...' : '保存并提交审核' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 弹窗: 手动合并建簇 -->
    <div v-if="showManualClusterModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="text-base font-bold text-slate-800">🧩 手动合并建簇 (已选 {{ selectedCaseIds.length }} 项)</h3>
          <button @click="showManualClusterModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">聚类簇标题 / 代表提问</label>
            <input v-model="manualClusterForm.cluster_name" type="text" placeholder="例如：空调高空作业安装收费规范" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">建议标准问法 (选填)</label>
            <input v-model="manualClusterForm.standard_question" type="text" placeholder="标准规范提问描述" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showManualClusterModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitManualCluster" :disabled="isSubmittingManualCluster" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold cursor-pointer disabled:opacity-50">
            {{ isSubmittingManualCluster ? '创建中...' : '确认合并建簇' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 弹窗: 单条 BadCase 独立采纳 -->
    <div v-if="showSingleAdoptModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="text-base font-bold text-slate-800">✨ 单条 BadCase 采纳治理</h3>
          <button @click="showSingleAdoptModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>
        <div class="space-y-3.5 text-xs flex-1 overflow-y-auto pr-1">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">采纳动作</label>
            <select v-model="singleAdoptForm.action" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="CREATE_FAQ">新建独立 FAQ (推荐)</option>
              <option value="ADD_SIMILAR_QUERY">追加相似问法至已有文档</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">标准问题</label>
            <input v-model="singleAdoptForm.standard_question" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-semibold text-indigo-900" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">标准答案</label>
            <textarea v-model="singleAdoptForm.answer" rows="4" placeholder="录入经过审核的标准官方解答..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showSingleAdoptModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitSingleAdopt" :disabled="isSubmittingSingleAdopt" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold cursor-pointer disabled:opacity-50">
            {{ isSubmittingSingleAdopt ? '提交中...' : '提交审核' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 弹窗: 单条 BadCase 独立驳回 -->
    <div v-if="showSingleRejectModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">🚫 单条 BadCase 驳回</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">驳回原因</label>
            <input v-model="singleRejectForm.reject_reason" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showSingleRejectModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitSingleReject" class="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-semibold cursor-pointer">确认驳回</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 A: 接新客户会话 -->
    <div v-if="showNewSessionModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">建立新客户咨询</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">客户姓名</label>
            <input v-model="newSessionForm.customer_name" type="text" placeholder="例如：李女士" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">客户唯一ID</label>
            <input v-model="newSessionForm.customer_id" type="text" placeholder="例如：user_1002" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono" />
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button @click="showNewSessionModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitCreateSession" class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer">建立</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 B: 新建知识库 -->
    <div v-if="showCreateKBDocModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">新建产品专属知识库</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">归属产品线编码</label>
            <select v-model="newKB.product_code" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono">
              <option value="SAAS_CLOUD">SAAS_CLOUD (企业SaaS云平台)</option>
              <option value="E_COMMERCE">E_COMMERCE (电商零售业务)</option>
              <option value="FIN_AI">FIN_AI (金融智能风控)</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">知识库名称</label>
            <input v-model="newKB.name" type="text" placeholder="例如：SaaS产品功能与售后政策库" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">详细描述</label>
            <textarea v-model="newKB.description" rows="3" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button @click="showCreateKBDocModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitCreateKB" class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer">保存创建</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 C: 检索阈值配置 -->
    <div v-if="showConfigModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">检索与重排参数调优【{{ editingKB.name }}】</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">高置信直接回复阈值 (Direct Threshold): {{ kbConfigForm.threshold_direct }}</label>
            <input v-model.number="kbConfigForm.threshold_direct" type="range" min="0.6" max="0.95" step="0.01" class="w-full" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">中置信推荐澄清阈值 (Clarify Threshold): {{ kbConfigForm.threshold_clarify }}</label>
            <input v-model.number="kbConfigForm.threshold_clarify" type="range" min="0.3" max="0.8" step="0.01" class="w-full" />
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">BM25 TopK</label>
              <input v-model.number="kbConfigForm.bm25_top_k" type="number" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">向量 TopK</label>
              <input v-model.number="kbConfigForm.vector_top_k" type="number" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">重排 TopK</label>
              <input v-model.number="kbConfigForm.rerank_top_k" type="number" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2" />
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button @click="showConfigModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="saveKBConfig" class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer">保存生效</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 D: 上传/新增知识文档 (重构版：清爽双Tab切换 + 切片Loading延迟遮罩) -->
    <div v-if="showUploadDocModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 relative overflow-hidden">
        
        <!-- Loading 遮罩层 (处理切片耗时延迟) -->
        <div v-if="isSubmittingDoc" class="absolute inset-0 bg-white/95 backdrop-blur-xs flex flex-col items-center justify-center gap-3 z-10">
          <div class="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p class="text-xs font-bold text-slate-800">正在解析文本并构建向量切片...</p>
          <p class="text-[11px] text-slate-500">（正在生成 Embedding 并入库，耗时约 2~4 秒，请稍候）</p>
        </div>

        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-800">添加知识文档</h3>
            <p class="text-[11px] text-slate-400 mt-0.5">支持本地文件上传或在线录入文本内容</p>
          </div>
          <button @click="showUploadDocModal = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold cursor-pointer">✕</button>
        </div>

        <!-- 模式切换 Tab -->
        <div class="grid grid-cols-2 p-1 bg-slate-100 rounded-xl text-xs font-medium">
          <button 
            type="button"
            @click="uploadDocTab = 'file'"
            :class="uploadDocTab === 'file' ? 'bg-white text-indigo-600 shadow-xs font-bold' : 'text-slate-500 hover:text-slate-700'"
            class="py-2 rounded-lg transition text-center cursor-pointer"
          >
            📁 本地文件上传
          </button>
          <button 
            type="button"
            @click="uploadDocTab = 'text'"
            :class="uploadDocTab === 'text' ? 'bg-white text-indigo-600 shadow-xs font-bold' : 'text-slate-500 hover:text-slate-700'"
            class="py-2 rounded-lg transition text-center cursor-pointer"
          >
            ✍️ 在线手动录入
          </button>
        </div>

        <div class="space-y-3.5 text-xs">
          <!-- 知识库选择与优先级配置 -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">归属知识库</label>
              <select v-model="newDoc.kb_id" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
                <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }} ({{ k.product_code }})</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">知识优先级 (1-5)</label>
              <select v-model.number="newDoc.priority" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
                <option :value="5">★ 5 极高 (优先召回)</option>
                <option :value="4">★ 4 高优先级</option>
                <option :value="3">★ 3 中等优先级</option>
                <option :value="2">★ 2 次要优先级</option>
                <option :value="1">★ 1 普通知识</option>
              </select>
            </div>
          </div>

          <!-- Tab 1: 本地文件上传 -->
          <div v-if="uploadDocTab === 'file'" class="space-y-3">
            <div class="border-2 border-dashed border-slate-200 hover:border-indigo-400 bg-slate-50/60 hover:bg-indigo-50/20 rounded-2xl p-6 text-center transition cursor-pointer" @click="$refs.fileInput.click()">
              <input type="file" ref="fileInput" @change="onFileSelected" accept=".md,.txt" class="hidden" />
              <div class="text-3xl mb-2">📄</div>
              <p class="font-bold text-slate-700">{{ selectedFileName || '点击选择本地 .md 或 .txt 文件' }}</p>
              <p class="text-[11px] text-slate-400 mt-1">系统将自动按照标题层级或段落语义智能分块</p>
            </div>
          </div>

          <!-- Tab 2: 在线录入 -->
          <div v-if="uploadDocTab === 'text'" class="space-y-3">
            <div class="grid grid-cols-3 gap-2">
              <div class="col-span-2">
                <label class="block font-semibold text-slate-700 mb-1">文档标题</label>
                <input v-model="newDoc.name" type="text" placeholder="例如：SaaS产品售后政策.md" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
              </div>
              <div>
                <label class="block font-semibold text-slate-700 mb-1">格式</label>
                <select v-model="newDoc.doc_type" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
                  <option value="MD">Markdown</option>
                  <option value="TXT">TXT纯文本</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">文档正文内容</label>
              <textarea v-model="newDoc.content" rows="6" placeholder="请在此输入或粘贴知识文档正文..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono leading-relaxed"></textarea>
            </div>
          </div>

          <!-- 审核提示 -->
          <div v-if="currentRole === 'tech_agent'" class="p-2.5 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800 flex items-center gap-2">
            <span>ℹ️</span>
            <span>当前为技术客服身份：提交后文档将进入【待审核】状态，超管审核通过后方生效并切片入库。</span>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showUploadDocModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 hover:bg-slate-50 font-medium cursor-pointer">取消</button>
          <button @click="submitCreateDoc" :disabled="isSubmittingDoc" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-500/20 transition disabled:opacity-50 cursor-pointer">
            {{ isSubmittingDoc ? '正在切片处理中...' : '提交并处理' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 弹窗 E: 批量导入 FAQ -->
    <div v-if="showFaqImportModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] flex flex-col">
        <h3 class="text-base font-bold text-slate-800">批量录入结构化 FAQ (标准问+相似问+答案)</h3>
        <div class="space-y-3 text-xs flex-1 overflow-y-auto pr-1">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">归属知识库</label>
            <select v-model="faqForm.kb_id" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5">
              <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }} ({{ k.product_code }})</option>
            </select>
          </div>
          <div class="space-y-2 border-t border-slate-100 pt-2">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-700">FAQ 条目列表</span>
              <button @click="addFaqRow" class="text-indigo-600 font-bold hover:underline cursor-pointer">+ 添加一条问答</button>
            </div>
            <div v-for="(item, idx) in faqForm.items" :key="idx" class="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2 relative">
              <div class="grid grid-cols-3 gap-2">
                <div class="col-span-2">
                  <label class="block font-medium text-slate-600 mb-1">标准问题</label>
                  <input v-model="item.standard_question" type="text" placeholder="例如：怎么重置密码" class="w-full bg-white border border-slate-200 rounded-lg p-2" />
                </div>
                <div>
                  <label class="block font-medium text-slate-600 mb-1">优先级 (1-5)</label>
                  <input v-model.number="item.priority" type="number" min="1" max="5" class="w-full bg-white border border-slate-200 rounded-lg p-2" />
                </div>
              </div>
              <div>
                <label class="block font-medium text-slate-600 mb-1">相似问法 (支持分号或换行隔开)</label>
                <input v-model="item.similar_questions_text" type="text" placeholder="忘记密码怎么办；如何找回密码" class="w-full bg-white border border-slate-200 rounded-lg p-2" />
              </div>
              <div>
                <label class="block font-medium text-slate-600 mb-1">标准解答</label>
                <textarea v-model="item.answer" rows="2" class="w-full bg-white border border-slate-200 rounded-lg p-2"></textarea>
              </div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showFaqImportModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitBatchFAQ" class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer">导入并切片</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 F: 版本历史与回滚 -->
    <div v-if="showVersionModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[85vh] flex flex-col">
        <div>
          <h3 class="text-base font-bold text-slate-800">文档历史版本与快照回滚</h3>
          <p class="text-xs text-slate-500 font-mono mt-0.5">文档: {{ selectedDoc.name }} (当前版本: v{{ selectedDoc.version }})</p>
        </div>
        <div class="flex-1 overflow-y-auto space-y-2 pr-1 text-xs">
          <div v-for="v in docVersions" :key="v.id" class="p-3 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-bold text-indigo-700">版本: v{{ v.version }}</span>
              <span class="text-slate-400 font-mono text-[10px]">{{ (v.created_at || '').slice(0, 16).replace('T', ' ') }}</span>
            </div>
            <p class="text-slate-600 font-mono text-[11px] line-clamp-2 bg-white p-2 rounded border border-slate-100">
              {{ v.content }}
            </p>
            <div class="flex justify-between items-center text-[10px] text-slate-400">
              <span>编辑提交人: {{ v.created_by || 'admin' }}</span>
              <button 
                v-if="v.version !== selectedDoc.version" 
                @click="rollbackVersion(v.version)" 
                class="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-lg transition cursor-pointer"
              >
                回滚至此版本 ➔
              </button>
              <span v-else class="text-emerald-600 font-bold">当前最新版本</span>
            </div>
          </div>
        </div>
        <div class="flex justify-end pt-2 border-t border-slate-100">
          <button @click="showVersionModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">关闭</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 G: 文档正文完整预览 -->
    <div v-if="showPreviewDocModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl space-y-4 max-h-[85vh] flex flex-col">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-800">{{ previewDocData.name }}</h3>
            <span class="text-[10px] font-mono text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded-md mt-1 inline-block">
              版本: v{{ previewDocData.version }} · 优先级: ★{{ previewDocData.priority }} · 状态: {{ previewDocData.status }}
            </span>
          </div>
          <button @click="showPreviewDocModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 bg-slate-50 border border-slate-200 rounded-xl font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed select-text">
          {{ previewDocData.content || '暂无文档正文' }}
        </div>
      </div>
    </div>

    <!-- 弹窗 H: 编辑文档内容 -->
    <div v-if="showEditDocModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">编辑知识文档 (版本递增与重新索引)</h3>
        <div class="space-y-3 text-xs">
          <div class="grid grid-cols-3 gap-2">
            <div class="col-span-2">
              <label class="block font-semibold text-slate-700 mb-1">文档名称</label>
              <input v-model="editDocForm.name" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">优先级 (1-5)</label>
              <input v-model.number="editDocForm.priority" type="number" min="1" max="5" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
            </div>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">文档正文内容</label>
            <textarea v-model="editDocForm.content" rows="8" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono"></textarea>
          </div>
          <div v-if="currentRole === 'tech_agent'" class="p-2.5 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800">
            ℹ️ 客服编辑后将进入【待审核】状态，超管审核后才会重新切片生效。
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showEditDocModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitSaveDocEdit" class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer">保存修改</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 I: 编辑知识库名称和描述 -->
    <div v-if="showEditKBModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">编辑知识库属性</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">知识库名称</label>
            <input v-model="editKBForm.name" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5" />
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">运行状态</label>
            <select v-model="editKBForm.status" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="ACTIVE">ACTIVE - 启用</option>
              <option value="INACTIVE">INACTIVE - 停用</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">描述信息</label>
            <textarea v-model="editKBForm.description" rows="3" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showEditKBModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="saveKBBasicInfo" class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer">保存修改</button>
        </div>
      </div>
    </div>

    <!-- 溯源切片详情抽屉 -->
    <div v-if="inspectingSource" class="fixed inset-y-0 right-0 max-w-md w-full bg-white shadow-2xl z-50 border-l border-slate-200 flex flex-col">
      <div class="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div>
          <h3 class="text-xs font-bold text-slate-900">溯源依据切片原文</h3>
          <p class="text-[10px] text-slate-400 font-mono mt-0.5">文档: {{ inspectingSource.doc_name }}</p>
        </div>
        <button @click="inspectingSource = null" class="text-slate-400 hover:text-slate-600 text-sm font-bold cursor-pointer">✕</button>
      </div>
      <div class="flex-1 overflow-y-auto p-4 space-y-3 text-xs leading-relaxed select-text">
        <div class="bg-indigo-50/60 p-3 rounded-xl border border-indigo-100 space-y-1 text-slate-700">
          <p><strong>章节路径:</strong> {{ inspectingSource.heading || '文档正文' }}</p>
          <p><strong>切片编号:</strong> #{{ inspectingSource.chunk_id }}</p>
        </div>
        <div>
          <h4 class="font-bold text-slate-800 mb-1">切片原始内容</h4>
          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 font-mono whitespace-pre-wrap text-slate-700">
            {{ inspectingSource.snippet }}
          </div>
        </div>
      </div>
    </div>

    <!-- 弹窗 J: 采纳 BadCase 簇生成知识草稿 (进入待审核流) -->
    <div v-if="showAdoptModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-800">一键采纳并生成知识草稿</h3>
            <p class="text-[11px] text-slate-400 mt-0.5">将聚类问题簇转化为标准 FAQ 或长效知识，提交后自动进入超管审核流</p>
          </div>
          <button @click="showAdoptModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>

        <div class="space-y-3.5 text-xs flex-1 overflow-y-auto pr-1">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">采纳治理动作</label>
            <div class="grid grid-cols-2 gap-2">
              <label class="flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer" :class="adoptForm.action === 'CREATE_FAQ' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold' : 'border-slate-200 text-slate-600'">
                <input type="radio" v-model="adoptForm.action" value="CREATE_FAQ" class="text-indigo-600" />
                <span>新建结构化 FAQ (推荐)</span>
              </label>
              <label class="flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer" :class="adoptForm.action === 'ADD_SIMILAR_QUERY' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold' : 'border-slate-200 text-slate-600'">
                <input type="radio" v-model="adoptForm.action" value="ADD_SIMILAR_QUERY" class="text-indigo-600" />
                <span>追加相似问法至已有文档</span>
              </label>
            </div>
          </div>

          <div v-if="adoptForm.action === 'ADD_SIMILAR_QUERY'">
            <label class="block font-semibold text-slate-700 mb-1">选择目标知识文档</label>
            <select v-model="adoptForm.target_doc_id" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="">请选择要追加的文档</option>
              <option v-for="d in documents" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">标准问题 (Standard Question)</label>
            <input v-model="adoptForm.standard_question" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-bold text-slate-900" />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">相似提问表达池 (Similar Queries，每行一个或分号隔开)</label>
            <textarea v-model="adoptForm.similar_questions_text" rows="4" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono leading-relaxed"></textarea>
            <p class="text-[10px] text-slate-400 mt-1">系统已将簇内聚类的用户多形态问法自动填入，可随时增减</p>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">标准解答内容 (Answer)</label>
            <textarea v-model="adoptForm.answer" rows="5" placeholder="请录入权威标准的业务解答方案..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 leading-relaxed"></textarea>
          </div>

          <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800 flex items-start gap-2">
            <span>ℹ️</span>
            <span><strong>审核流提示：</strong>点击提交后，将在当前知识库中生成状态为 <span class="font-mono font-bold text-amber-900">PENDING_REVIEW</span> 的知识草稿，由超级管理员审核通过后，才正式构建向量索引生效，防止未经校验的数据污染检索库。</span>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showAdoptModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitAdoptCluster" :disabled="isSubmittingAdopt" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-500/20 cursor-pointer disabled:opacity-50">
            {{ isSubmittingAdopt ? '提交中...' : '确认采纳并提交审核' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 弹窗 K: 手动关联已有知识 -->
    <div v-if="showLinkModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">关联至已有知识文档</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">选择匹配的知识文档</label>
            <select v-model="linkForm.target_doc_id" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5">
              <option value="">请选择文档</option>
              <option v-for="d in documents" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">关联与处理说明</label>
            <textarea v-model="linkForm.notes" rows="3" placeholder="例如：该簇问法与已有售后文档第3条吻合，已追加至相似语义范围" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showLinkModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitLinkCluster" class="px-4 py-2 rounded-xl bg-sky-600 text-white text-xs font-semibold cursor-pointer">确认关联</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 L: 驳回无效 Case 簇 -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-slate-800">驳回无效问题簇</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">驳回原因 (移出待办池)</label>
            <select v-model="rejectForm.reason_select" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 mb-2 font-medium">
              <option value="闲聊或非业务支持类提问">闲聊或非业务支持类提问</option>
              <option value="用户连续错别字或无意义乱码">用户连续错别字或无意义乱码</option>
              <option value="超出当前企业支持范围">超出当前企业支持范围</option>
              <option value="重复偶发测试用例">重复偶发测试用例</option>
              <option value="OTHER">其他原因 (手动录入)</option>
            </select>
            <textarea v-model="rejectForm.reject_reason" rows="3" placeholder="请输入具体驳回理由..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showRejectModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitRejectCluster" class="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-semibold cursor-pointer">确认驳回</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 M: 效果回流回归测试报告 -->
    <div v-if="showValidationModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-800">🧪 效果回流回归测试报告</h3>
            <p class="text-[11px] text-slate-400 mt-0.5">针对该簇所有历史真实问句执行检索召回与重排打分，自动化检验闭环成效</p>
          </div>
          <button @click="showValidationModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>

        <!-- 核心达标指标卡 -->
        <div class="p-4 rounded-xl flex items-center justify-between"
             :class="validationReport.pass_rate >= 0.75 ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'">
          <div>
            <span class="text-xs font-semibold" :class="validationReport.pass_rate >= 0.75 ? 'text-emerald-800' : 'text-amber-800'">
              测试簇: {{ validationReport.cluster_name }}
            </span>
            <p class="text-[11px] mt-0.5" :class="validationReport.pass_rate >= 0.75 ? 'text-emerald-600' : 'text-amber-600'">
              {{ validationReport.pass_rate >= 0.75 ? '🎉 回归效果达标，该问题簇已成功闭环解决！' : '⚠️ 部分变体问法检索置信度未达到阈值，建议继续追加相似问或等待审核生效。' }}
            </p>
          </div>
          <div class="text-right">
            <div class="text-2xl font-black font-mono" :class="validationReport.pass_rate >= 0.75 ? 'text-emerald-700' : 'text-amber-700'">
              {{ ((validationReport.pass_rate || 0) * 100).toFixed(1) }}%
            </div>
            <span class="text-[10px] font-mono text-slate-500">通过率 (Pass Rate)</span>
          </div>
        </div>

        <!-- 逐条 Query 回归结果列表 -->
        <div class="flex-1 overflow-y-auto space-y-2 pr-1 text-xs">
          <table class="w-full text-left text-xs text-slate-700 border border-slate-200 rounded-xl overflow-hidden">
            <thead class="bg-slate-50 border-b border-slate-200 text-[10px] text-slate-500 font-semibold uppercase">
              <tr>
                <th class="py-2.5 px-3">测试用例提问 (Query)</th>
                <th class="py-2.5 px-3 w-24 text-center">状态</th>
                <th class="py-2.5 px-3 w-28 text-center">检索置信度</th>
                <th class="py-2.5 px-3">命中文档/章节</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="(item, idx) in (validationReport.details || validationReport.items || [])" :key="idx" class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-medium text-slate-900">{{ item.query }}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono"
                        :class="item.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'">
                    {{ item.passed ? '✅ 通过' : '❌ 未达标' }}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center font-mono font-bold"
                    :class="(item.top_score != null ? item.top_score : item.score) >= 0.70 ? 'text-emerald-600' : 'text-amber-600'">
                  {{ (((item.top_score != null ? item.top_score : item.score) || 0) * 100).toFixed(1) }}%
                </td>
                <td class="py-2.5 px-3 text-[11px] text-slate-500 truncate max-w-xs">
                  {{ item.top_heading || item.top_doc || item.matched_heading || '未命中有效切片' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex justify-end pt-2 border-t border-slate-100">
          <button @click="showValidationModal = false" class="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold cursor-pointer">关闭报告</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 N: 用户对话差评原因收集 -->
    <div v-if="showFeedbackModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="text-base font-bold text-slate-800">💡 告诉我们哪里不够满意</h3>
          <button @click="showFeedbackModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1.5">主要原因</label>
            <div class="grid grid-cols-2 gap-2">
              <button 
                type="button" 
                v-for="r in ['答非所问', '内容有错误', '解释不够清晰', '信息已过时', '未解决问题', '其它原因']" 
                :key="r"
                @click="feedbackForm.selectedReason = r"
                class="p-2 rounded-xl border text-left transition font-medium cursor-pointer"
                :class="feedbackForm.selectedReason === r ? 'border-rose-500 bg-rose-50/50 text-rose-800 font-bold' : 'border-slate-200 text-slate-600 hover:bg-slate-50'"
              >
                {{ r }}
              </button>
            </div>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">补充说明 (选填)</label>
            <textarea v-model="feedbackForm.comment" rows="3" placeholder="请详细描述您遇到的问题，帮助我们训练优化..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showFeedbackModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitUserFeedback" class="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-semibold cursor-pointer">提交差评反馈</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 O: 坐席人工错误标注 -->
    <div v-if="showAgentLabelModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="text-base font-bold text-slate-800">🏷️ 坐席客服 BadCase 质检标错</h3>
          <button @click="showAgentLabelModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">错误分类</label>
            <select v-model="agentLabelForm.label_category" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="WRONG_ANSWER">AI回答严重错误 (与政策相悖)</option>
              <option value="IRRELEVANT">答非所问 / 召回知识错位</option>
              <option value="MISSING_KNOWLEDGE">知识库缺失 (业务盲区)</option>
              <option value="OUTDATED">答案陈旧过时 (规则已更新)</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">坐席质检备注说明</label>
            <textarea v-model="agentLabelForm.notes" rows="3" placeholder="请简要指出具体错误点，供运营人员定向优化..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showAgentLabelModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitAgentLabel" class="px-4 py-2 rounded-xl bg-amber-600 text-white text-xs font-semibold cursor-pointer">提交标注入库</button>
        </div>
      </div>
    </div>

    <!-- 弹窗 P: 闭环转化漏斗全景看板 -->
    <div v-if="showAnalyticsModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-800">📊 BadCase 治理闭环转化全景看板</h3>
            <p class="text-[11px] text-slate-400 mt-0.5">全流程指标度量：采集 ➔ 聚类 ➔ 采纳转化 ➔ 检索回归验证</p>
          </div>
          <button @click="showAnalyticsModal = false" class="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">✕</button>
        </div>

        <!-- 漏斗阶段示意 -->
        <div class="grid grid-cols-4 gap-2 text-center text-xs">
          <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
            <div class="text-[10px] text-slate-400 font-medium">1. 进线采集</div>
            <div class="text-xl font-bold font-mono text-slate-800">{{ dashboardStats.total_cases_collected || 0 }} 笔</div>
            <div class="text-[9px] text-slate-400">差评+低置信+坐席</div>
          </div>
          <div class="p-3 bg-indigo-50/60 rounded-xl border border-indigo-200 space-y-1">
            <div class="text-[10px] text-indigo-600 font-medium">2. 凝聚聚类</div>
            <div class="text-xl font-bold font-mono text-indigo-700">{{ dashboardStats.total_clusters || 0 }} 簇</div>
            <div class="text-[9px] text-indigo-500">语义向量聚类</div>
          </div>
          <div class="p-3 bg-amber-50 rounded-xl border border-amber-200 space-y-1">
            <div class="text-[10px] text-amber-600 font-medium">3. 运营采纳草稿</div>
            <div class="text-xl font-bold font-mono text-amber-700">{{ dashboardStats.adopted_clusters || 0 }} 簇</div>
            <div class="text-[9px] text-amber-500">转化为待审核FAQ/相似问</div>
          </div>
          <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 space-y-1">
            <div class="text-[10px] text-emerald-600 font-medium">4. 回归达标率</div>
            <div class="text-xl font-bold font-mono text-emerald-700">{{ dashboardStats.average_pass_rate || 0 }}%</div>
            <div class="text-[9px] text-emerald-500">回流验证平均达标率</div>
          </div>
        </div>

        <!-- 细分来源分布 -->
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
          <h4 class="font-bold text-slate-800">BadCase 采集来源构成</h4>
          <div class="space-y-2">
            <div>
              <div class="flex justify-between text-[11px] mb-1">
                <span>用户前台点差评 (USER_FEEDBACK)</span>
                <span class="font-mono font-bold">{{ dashboardStats.case_types?.user_feedback || 0 }} 笔</span>
              </div>
              <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-rose-500 h-2 rounded-full" :style="{ width: ((dashboardStats.case_types?.user_feedback || 0) / (dashboardStats.total_cases_collected || 1) * 100) + '%' }"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between text-[11px] mb-1">
                <span>低置信度/兜底未命中自动录入 (LOW_CONFIDENCE)</span>
                <span class="font-mono font-bold">{{ dashboardStats.case_types?.low_confidence || 0 }} 笔</span>
              </div>
              <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-sky-500 h-2 rounded-full" :style="{ width: ((dashboardStats.case_types?.low_confidence || 0) / (dashboardStats.total_cases_collected || 1) * 100) + '%' }"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between text-[11px] mb-1">
                <span>坐席控制台人工质检标注 (AGENT_LABEL)</span>
                <span class="font-mono font-bold">{{ dashboardStats.case_types?.agent_label || 0 }} 笔</span>
              </div>
              <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-amber-500 h-2 rounded-full" :style="{ width: ((dashboardStats.case_types?.agent_label || 0) / (dashboardStats.total_cases_collected || 1) * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end pt-2 border-t border-slate-100">
          <button @click="showAnalyticsModal = false" class="px-5 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold cursor-pointer">关闭</button>
        </div>
      </div>
    </div>

  </div> <!-- 关闭 #app -->

  <script>
    const { createApp, ref, reactive, computed, onMounted, nextTick } = Vue;

    createApp({
      setup() {
        // ================= 1. 同步读取登录态（彻底解决刷新切换角色 Bug） =================
        const savedUser = (() => {
          try {
            const raw = localStorage.getItem('smart_cs_user');
            return raw ? JSON.parse(raw) : null;
          } catch (e) {
            return null;
          }
        })();

        const isLoggedIn = ref(!!savedUser);
        const currentRole = ref(savedUser ? (savedUser.role || 'user') : 'user');
        const currentUserId = ref(savedUser ? (savedUser.user_id || 'user_001') : 'user_001');
        const currentUsername = ref(savedUser ? (savedUser.username || 'user') : 'user');
        const currentUserDisplayName = ref(savedUser ? (savedUser.display_name || '普通客户') : '普通客户');
        const currentUserProduct = ref(savedUser ? (savedUser.product_code || '') : '');

        const loginForm = reactive({ username: '', password: '' });
        const loginError = ref('');
        const loginLoading = ref(false);

        const assignedKbId = ref(savedUser ? (savedUser.assigned_kb_id || '') : '');

        const roleLabels = {
          user: '普通客户',
          tech_agent: '技术客服',
          admin: '超级管理员',
          operator: '知识运营'
        };
        const roleLabel = computed(() => {
          if (currentRole.value === 'tech_agent') {
            return currentUserProduct.value === 'E_COMMERCE' ? '电商技术客服' : 'SaaS技术客服';
          }
          if (currentRole.value === 'operator') {
            return assignedKbId.value === 'kb_saas_cloud_02' ? 'SaaS知识运营' : '电商知识运营';
          }
          return roleLabels[currentRole.value] || '客户';
        });

        const hasMenuPermission = (menuKey) => {
          if (menuKey === 'chat') return currentRole.value !== 'operator';
          if (menuKey === 'chunks') return currentRole.value === 'admin' || currentRole.value === 'tech_agent' || currentRole.value === 'operator';
          if (menuKey === 'kb') return currentRole.value === 'admin';
          if (menuKey === 'badcases') return currentRole.value === 'admin' || currentRole.value === 'operator';
          return false;
        };

        const assignedKbName = computed(() => {
          if (!assignedKbId.value) return '所属专属知识库';
          const k = kbs.value.find(x => x.id === assignedKbId.value);
          return k ? k.name : '电商标准售后与服务知识库';
        });

        const getKbNameById = (kId) => {
          const k = kbs.value.find(x => x.id === kId);
          return k ? k.name : (kId || '默认知识库');
        };

        const canManageHumanSession = computed(() => {
          return currentRole.value === 'admin' || currentRole.value === 'tech_agent';
        });

        // 统一附带权限与隔离上下文请求头
        const authFetch = (url, options = {}) => {
          const headers = options.headers || {};
          headers['X-User-Role'] = currentRole.value;
          headers['X-User-Id'] = currentUserId.value;
          if (currentUserProduct.value) {
            headers['X-User-Product'] = currentUserProduct.value;
          }
          if (assignedKbId && assignedKbId.value) {
            headers['X-User-Kb-Id'] = assignedKbId.value;
          }
          return fetch(url, { ...options, headers });
        };

        // ================= 2. 核心状态与数据模型 =================
        const activeMenu = ref('chat');
        const currentProductCode = ref(currentUserProduct.value || 'SAAS_CLOUD');

        // 会话与消息流
        const sessions = ref([]);
        const currentSession = ref(null);
        const messageList = ref([]);
        const sessionFilterStatus = ref('ACTIVE'); // 'ACTIVE', 'CLOSED', 'ALL'
        const newAssignmentAlert = ref(null);
        const knownAssignedIds = new Set();

        const filteredSessions = computed(() => {
          if (currentRole.value === 'user') {
            return sessions.value.filter(s => s.customer_id === currentUserId.value);
          }
          if (currentRole.value === 'tech_agent') {
            // 技术客服：只展示分配给自己的活跃会话
            return sessions.value.filter(s => s.assigned_agent === currentUserId.value && s.status !== 'CLOSED');
          }
          // 超级管理员：可按状态筛选
          if (sessionFilterStatus.value === 'ACTIVE') {
            return sessions.value.filter(s => s.status !== 'CLOSED');
          } else if (sessionFilterStatus.value === 'CLOSED') {
            return sessions.value.filter(s => s.status === 'CLOSED');
          }
          return sessions.value;
        });

        const inputQuery = ref('');
        const isThinking = ref(false);
        const chatContainer = ref(null);
        const inspectingSource = ref(null);

        // 知识库与文档
        const kbs = ref([]);
        const chunkViewTab = ref('docs');
        const documents = ref([]);
        const chunkList = ref([]);
        const filterKbId = ref('');
        const filterDocType = ref('');
        const filterDocStatus = ref('');
        const filterDocId = ref('');
        const searchKeyword = ref('');

        // 图三重构状态：双Tab切换与切片耗时遮罩
        const showUploadDocModal = ref(false);
        const uploadDocTab = ref('file'); // 'file' 或 'text'
        const isSubmittingDoc = ref(false);
        const selectedFileName = ref('');
        const fileInput = ref(null);
        const newDoc = reactive({ kb_id: '', name: '', doc_type: 'MD', priority: 3, content: '' });

        // 其他弹窗
        const showNewSessionModal = ref(false);
        const newSessionForm = reactive({ customer_name: '', customer_id: '' });

        const showCreateKBDocModal = ref(false);
        const newKB = reactive({ product_code: 'SAAS_CLOUD', name: '', description: '' });

        const showConfigModal = ref(false);
        const editingKB = ref({});
        const kbConfigForm = reactive({ threshold_direct: 0.80, threshold_clarify: 0.50, bm25_top_k: 15, vector_top_k: 15, rerank_top_k: 3 });

        const showEditKBModal = ref(false);
        const editKBForm = reactive({ name: '', description: '', status: 'ACTIVE' });

        const showFaqImportModal = ref(false);
        const faqForm = reactive({ kb_id: '', items: [{ standard_question: '', similar_questions_text: '', answer: '', priority: 3 }] });

        const showVersionModal = ref(false);
        const selectedDoc = ref({});
        const docVersions = ref([]);

        const showPreviewDocModal = ref(false);
        const previewDocData = ref({});

        const showEditDocModal = ref(false);
        const editDocForm = reactive({ id: '', name: '', priority: 3, content: '', version: 1 });

        // 辅助函数：根据 kb_id 查询真实知识库名称（图一修复）
        const getKbName = (kbId) => {
          const k = kbs.value.find(item => item.id === kbId);
          return k ? k.name : '产品知识库';
        };

        // ================= 3. 业务 API 与会话流转 =================

        // 普通客户开启全新空白会话（重新登录或进入时触发，不复用历史）
        const initCustomerNewSession = async (forceNew = true) => {
          currentSession.value = null;
          messageList.value = [];
          try {
            const custId = currentUserId.value || ('cust_' + Math.floor(Math.random() * 9000 + 1000));
            currentUserId.value = custId;
            const res = await authFetch('/api/v1/chat/sessions', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                customer_id: custId,
                customer_name: currentUserDisplayName.value || `客户 · ${custId}`,
                product_code: currentProductCode.value,
                force_new: forceNew
              })
            });
            if (res.ok) {
              const sess = await res.json();
              currentSession.value = sess;
              scrollToBottom();
            }
          } catch (e) {
            console.error('初始化客户会话失败', e);
          }
        };

        // 拉取所有会话列表并进行实时状态检查与分配提醒
        const fetchSessions = async () => {
          if (currentRole.value === 'user') return;
          try {
            const res = await authFetch('/api/v1/chat/sessions');
            if (res.ok) {
              const data = await res.json();
              sessions.value = data;

              // 技术客服：检测新分配工单提醒
              if (currentRole.value === 'tech_agent') {
                data.forEach(s => {
                  if (s.assigned_agent === currentUserId.value && s.status === 'HUMAN_CONNECTED') {
                    if (!knownAssignedIds.has(s.id)) {
                      knownAssignedIds.add(s.id);
                      // 若不是当前正在查看的会话，触发弹窗提醒
                      if (!currentSession.value || currentSession.value.id !== s.id) {
                        newAssignmentAlert.value = s;
                      }
                    }
                  }
                });
              }

              // 同步当前选中的会话状态
              if (currentSession.value) {
                const refreshed = data.find(x => x.id === currentSession.value.id);
                if (refreshed) {
                  currentSession.value.status = refreshed.status;
                  currentSession.value.assigned_agent = refreshed.assigned_agent;
                  currentSession.value.last_message = refreshed.last_message;
                }
              } else if (filteredSessions.value.length > 0) {
                await switchSession(filteredSessions.value[0]);
              }
            }
          } catch (e) {
            console.error('加载会话列表失败', e);
          }
        };

        const handleJumpToAssignedSession = async (sess) => {
          newAssignmentAlert.value = null;
          await switchSession(sess);
        };

        const switchSession = async (s) => {
          currentSession.value = s;
          currentProductCode.value = s.product_code;
          inspectingSource.value = null;
          try {
            const res = await authFetch(`/api/v1/chat/sessions/${s.id}/messages`);
            if (res.ok) {
              messageList.value = await res.json();
              scrollToBottom();
            }
          } catch (e) {
            console.error('加载会话消息失败', e);
          }
        };

        const onUserProductChange = async () => {
          if (currentRole.value === 'user') {
            await initCustomerNewSession(true);
          }
        };

        // 定时轮询同步消息与状态（防竞态：思考中不覆盖列表）
        let pollTimer = null;
        const syncSessionMessages = async () => {
          if (!isLoggedIn.value) return;

          // 客服或超管角色：每轮刷新会话列表，实时感知用户接入与状态变化（免手动刷新）
          if (currentRole.value !== 'user') {
            await fetchSessions();
          }

          if (!currentSession.value || isThinking.value) return;

          try {
            const res = await authFetch(`/api/v1/chat/sessions/${currentSession.value.id}/messages`);
            if (res.ok) {
              const msgs = await res.json();
              if (msgs && msgs.length > 0) {
                const curLen = messageList.value.length;
                if (msgs.length > curLen || (curLen > 0 && msgs[msgs.length - 1].id !== messageList.value[curLen - 1].id)) {
                  messageList.value = msgs;
                  scrollToBottom();
                }
              }
            }
          } catch (e) {}
        };

        const startPolling = () => {
          stopPolling();
          pollTimer = setInterval(syncSessionMessages, 2500);
        };

        const stopPolling = () => {
          if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
          }
        };

        // 发送消息（严格防吞、防崩溃）
        const handleSend = async () => {
          const q = inputQuery.value.trim();
          if (!q || isThinking.value || !currentSession.value) return;

          const tempMsg = {
            id: 'temp_' + Date.now(),
            role: currentRole.value === 'user' ? 'user' : 'human_agent',
            content: q,
            created_at: new Date().toISOString()
          };
          messageList.value.push(tempMsg);
          inputQuery.value = '';
          isThinking.value = true;
          scrollToBottom();

          try {
            const resp = await authFetch('/api/v1/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                product_code: currentProductCode.value,
                customer_id: currentSession.value.customer_id,
                session_id: currentSession.value.id,
                query: q
              })
            });

            if (!resp.ok) {
              const err = await resp.json().catch(() => ({}));
              messageList.value.push({
                id: 'err_' + Date.now(),
                role: 'assistant',
                reply_type: 'FALLBACK',
                confidence_score: 0.0,
                content: `⚠️ 对话服务提示: ${err.detail || '检索服务繁忙，请稍后重试'}`,
                created_at: new Date().toISOString()
              });
              return;
            }

            const data = await resp.json();
            if (currentRole.value === 'user') {
              messageList.value.push({
                id: 'ai_' + Date.now(),
                role: data.reply_type === 'HUMAN_AGENT' ? 'human_agent' : 'assistant',
                reply_type: data.reply_type,
                confidence_score: data.confidence_score,
                content: data.content,
                raw_query: data.raw_query,
                rewritten_query: data.rewritten_query,
                sources: data.sources || [],
                suggested_questions: data.suggested_questions || [],
                business_data: data.business_data || null,
                created_at: new Date().toISOString()
              });
            }
            currentSession.value.last_message = q;
          } catch (e) {
            messageList.value.push({
              id: 'net_err_' + Date.now(),
              role: 'assistant',
              reply_type: 'FALLBACK',
              confidence_score: 0.0,
              content: '网络连接出现波动，未能送达您的消息，请重试。'
            });
          } finally {
            isThinking.value = false;
            scrollToBottom();
          }
        };

        const sendQuickPrompt = (txt) => {
          inputQuery.value = txt;
          handleSend();
        };

        // 用户转接人工座席
        const handleManualTransferHuman = async () => {
          if (!currentSession.value) return;
          try {
            const res = await authFetch('/api/v1/chat/transfer-human', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                session_id: currentSession.value.id,
                customer_id: currentSession.value.customer_id
              })
            });
            if (res.ok) {
              const result = await res.json();
              currentSession.value.status = 'HUMAN_CONNECTED';
              currentSession.value.assigned_agent = result.agent;
              const msgRes = await authFetch(`/api/v1/chat/sessions/${currentSession.value.id}/messages`);
              if (msgRes.ok) {
                messageList.value = await msgRes.json();
                scrollToBottom();
              }
            }
          } catch (e) {
            console.error('转人工失败', e);
          }
        };

        // 用户主动挂断人工服务
        const handleUserHangup = async () => {
          if (!currentSession.value) return;
          try {
            const res = await authFetch(`/api/v1/chat/hangup?session_id=${currentSession.value.id}`, { method: 'POST' });
            if (res.ok) {
              currentSession.value.status = 'AI_SERVICE';
              currentSession.value.assigned_agent = null;
              const msgRes = await authFetch(`/api/v1/chat/sessions/${currentSession.value.id}/messages`);
              if (msgRes.ok) {
                messageList.value = await msgRes.json();
                scrollToBottom();
              }
            }
          } catch (e) {
            console.error('挂断人工失败', e);
          }
        };

        // 客服/超管结束人工服务
        const finishHumanService = async () => {
          if (!currentSession.value) return;
          try {
            const res = await authFetch(`/api/v1/chat/finish-human?session_id=${currentSession.value.id}`, { method: 'POST' });
            if (res.ok) {
              currentSession.value.status = 'AI_SERVICE';
              currentSession.value.assigned_agent = null;
              const msgRes = await authFetch(`/api/v1/chat/sessions/${currentSession.value.id}/messages`);
              if (msgRes.ok) {
                messageList.value = await msgRes.json();
                scrollToBottom();
              }
            }
          } catch (e) {
            console.error('结束人工失败', e);
          }
        };

        const openSourceDrawer = (src) => {
          inspectingSource.value = src;
        };

        const scrollToBottom = () => {
          nextTick(() => {
            if (chatContainer.value) {
              chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
            }
          });
        };

        // ================= 4. 知识库与文档 API (修复图一名称、删除联动与审核流) =================

        // 拉取知识库列表（技术客服直接调用，拿真实名称，消除图一的哈希截断名称）
        const fetchKBs = async () => {
          try {
            const res = await authFetch('/api/v1/kbs');
            if (res.ok) {
              kbs.value = await res.json();
              if (kbs.value.length > 0 && !newDoc.kb_id) {
                newDoc.kb_id = kbs.value[0].id;
                faqForm.kb_id = kbs.value[0].id;
              }
            }
          } catch (e) {
            console.error('加载知识库失败', e);
          }
        };

        const onFilterKbChange = async () => {
          filterDocId.value = '';
          await refreshDocAndChunks();
        };

        const onFilterDocChange = async () => {
          await refreshChunks();
        };

        const refreshDocs = async () => {
          if (!hasMenuPermission('chunks')) return;
          let url = `/api/v1/documents?page=1&page_size=100`;
          if (filterKbId.value) url += `&kb_id=${filterKbId.value}`;
          if (filterDocType.value) url += `&doc_type=${filterDocType.value}`;
          if (filterDocStatus.value) url += `&status=${filterDocStatus.value}`;
          if (searchKeyword.value) url += `&name=${encodeURIComponent(searchKeyword.value.trim())}`;
          try {
            const res = await authFetch(url);
            if (res.ok) {
              documents.value = await res.json();
            }
          } catch (e) {}
        };

        const refreshChunks = async () => {
          if (!hasMenuPermission('chunks')) return;
          let url = `/api/v1/chunks?page=1&page_size=50`;
          if (filterDocId.value) {
            url += `&doc_id=${filterDocId.value}`;
          } else if (filterKbId.value) {
            url += `&kb_id=${filterKbId.value}`;
          }
          if (searchKeyword.value && searchKeyword.value.trim()) {
            url += `&keyword=${encodeURIComponent(searchKeyword.value.trim())}`;
          }
          try {
            const res = await authFetch(url);
            if (res.ok) {
              const data = await res.json();
              chunkList.value = data.items || [];
            }
          } catch (e) {}
        };

        const refreshDocAndChunks = async () => {
          await refreshDocs();
          await refreshChunks();
        };

        const handleSearch = () => {
          refreshDocAndChunks();
        };

        // 超管审核流操作
        const approveDoc = async (doc) => {
          if (confirm(`确认批准文档【${doc.name}】生效并立即生成高维向量切片？`)) {
            const res = await authFetch(`/api/v1/documents/${doc.id}/approve`, { method: 'POST' });
            if (res.ok) {
              const resData = await res.json();
              alert(resData.message || '文档已成功批准并生效！');
              await fetchKBs();
              await refreshDocAndChunks();
            } else {
              alert('审核操作失败');
            }
          }
        };

        const rejectDoc = async (doc) => {
          const reason = prompt('请输入驳回理由:', '文档内容不合规或缺少格式');
          if (reason !== null) {
            const res = await authFetch(`/api/v1/documents/${doc.id}/reject?reason=${encodeURIComponent(reason)}`, { method: 'POST' });
            if (res.ok) {
              alert('该文档已被驳回');
              await refreshDocAndChunks();
            }
          }
        };

        // 删除知识库（前端实时级联消除，无需刷新）
        const confirmDeleteKB = async (kb) => {
          if (confirm(`⚠️ 危险操作：确认删除知识库【${kb.name}】吗？\n将级联删除其下的所有知识文档、切片及向量索引！`)) {
            const res = await authFetch(`/api/v1/kbs/${kb.id}`, { method: 'DELETE' });
            if (res.status === 403) return alert('权限不足：仅超级管理员可执行级联删除操作！');
            
            // 实时前端响应式删除，无需刷新页面
            kbs.value = kbs.value.filter(k => k.id !== kb.id);
            documents.value = documents.value.filter(d => d.kb_id !== kb.id);
            chunkList.value = chunkList.value.filter(c => c.kb_id !== kb.id);
            if (filterKbId.value === kb.id) {
              filterKbId.value = '';
              filterDocId.value = '';
            }
            alert(`知识库【${kb.name}】及其全部文档和切片已成功级联删除！`);
          }
        };

        // 图三重构：打开弹窗并选择文件
        const openUploadModal = () => {
          uploadDocTab.value = 'file';
          selectedFileName.value = '';
          newDoc.name = '';
          newDoc.content = '';
          isSubmittingDoc.value = false;
          showUploadDocModal.value = true;
        };

        const onFileSelected = (e) => {
          if (e.target.files && e.target.files[0]) {
            selectedFileName.value = e.target.files[0].name;
          }
        };

        // 提交上传/录入文档（含 Loading 与防重）
        const submitCreateDoc = async () => {
          if (!newDoc.kb_id) {
            return alert('请先选择归属知识库');
          }

          isSubmittingDoc.value = true;
          try {
            if (uploadDocTab.value === 'file') {
              if (!fileInput.value || !fileInput.value.files || !fileInput.value.files[0]) {
                isSubmittingDoc.value = false;
                return alert('请先点击虚线框选择本地 .md 或 .txt 文件');
              }
              const formData = new FormData();
              formData.append('kb_id', newDoc.kb_id);
              formData.append('priority', newDoc.priority || 3);
              formData.append('file', fileInput.value.files[0]);
              formData.append('created_by', roleLabel.value);

              const res = await authFetch('/api/v1/documents/upload', {
                method: 'POST',
                body: formData
              });
              if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                isSubmittingDoc.value = false;
                return alert(err.detail || '上传文档失败');
              }
              const resData = await res.json();
              if (currentRole.value === 'tech_agent') {
                alert('文档提交成功！已进入【待审核】队列，等待超级管理员审批后切片生效。');
              } else {
                alert('文档上传并向量切片成功！');
              }
            } else {
              if (!newDoc.name || !newDoc.content) {
                isSubmittingDoc.value = false;
                return alert('请填写文档标题和正文内容');
              }
              const res = await authFetch('/api/v1/documents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newDoc)
              });
              if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                isSubmittingDoc.value = false;
                return alert(err.detail || '创建文档失败');
              }
              if (currentRole.value === 'tech_agent') {
                alert('在线文档提交成功！已进入【待审核】队列，超管审批后生效。');
              } else {
                alert('知识文档创建并切片成功！');
              }
            }

            showUploadDocModal.value = false;
            newDoc.name = '';
            newDoc.content = '';
            selectedFileName.value = '';
            if (fileInput.value) fileInput.value.value = '';
            await fetchKBs();
            await refreshDocAndChunks();
          } catch (e) {
            alert('网络错误，请稍后重试');
          } finally {
            isSubmittingDoc.value = false;
          }
        };

        const submitCreateKB = async () => {
          if (!newKB.name) return alert('请填写知识库名称');
          const res = await authFetch('/api/v1/kbs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newKB)
          });
          if (res.status === 403) return alert('权限不足：仅超级管理员可创建知识库！');
          if (res.ok) {
            showCreateKBDocModal.value = false;
            newKB.name = '';
            newKB.description = '';
            await fetchKBs();
          } else {
            const err = await res.json();
            alert(err.detail || '创建失败');
          }
        };

        const toggleKBStatus = async (kb) => {
          const newStatus = kb.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
          const res = await authFetch(`/api/v1/kbs/${kb.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
          });
          if (res.status === 403) return alert('权限不足：仅超级管理员可操作！');
          if (res.ok) {
            kb.status = newStatus;
          }
        };

        const openEditKBModal = (kb) => {
          editKBForm.id = kb.id;
          editKBForm.name = kb.name;
          editKBForm.description = kb.description || '';
          editKBForm.status = kb.status;
          showEditKBModal.value = true;
        };

        const saveKBBasicInfo = async () => {
          const res = await authFetch(`/api/v1/kbs/${editKBForm.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: editKBForm.name,
              description: editKBForm.description,
              status: editKBForm.status
            })
          });
          if (res.status === 403) return alert('权限不足！');
          showEditKBModal.value = false;
          await fetchKBs();
        };

        const openConfigModal = (kb) => {
          editingKB.value = kb;
          const cfg = kb.config || {};
          kbConfigForm.threshold_direct = cfg.threshold_direct || 0.80;
          kbConfigForm.threshold_clarify = cfg.threshold_clarify || 0.50;
          kbConfigForm.bm25_top_k = cfg.bm25_top_k || 15;
          kbConfigForm.vector_top_k = cfg.vector_top_k || 15;
          kbConfigForm.rerank_top_k = cfg.rerank_top_k || 3;
          showConfigModal.value = true;
        };

        const saveKBConfig = async () => {
          const res = await authFetch(`/api/v1/kbs/${editingKB.value.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: kbConfigForm })
          });
          if (res.status === 403) return alert('权限不足！');
          showConfigModal.value = false;
          await fetchKBs();
          alert('知识库检索阈值与TopK参数已更新生效！');
        };

        const openPreviewDoc = (doc) => {
          previewDocData.value = doc;
          showPreviewDocModal.value = true;
        };

        const openEditDocModal = (doc) => {
          editDocForm.id = doc.id;
          editDocForm.name = doc.name;
          editDocForm.priority = doc.priority;
          editDocForm.content = doc.content || '';
          editDocForm.version = doc.version;
          showEditDocModal.value = true;
        };

        const submitSaveDocEdit = async () => {
          if (!editDocForm.name || !editDocForm.content) return alert('文档标题和内容不能为空');
          const res = await authFetch(`/api/v1/documents/${editDocForm.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: editDocForm.name,
              priority: editDocForm.priority,
              content: editDocForm.content
            })
          });
          if (res.status === 403) return alert('权限不足！');
          showEditDocModal.value = false;
          await fetchKBs();
          await refreshDocAndChunks();
          if (currentRole.value === 'tech_agent') {
            alert('修改已保存，由于您是技术客服，修改已进入【待审核】状态，超管审批通过后切片更新。');
          } else {
            alert('文档已成功更新，新版本已生效并重新切片！');
          }
        };

        const viewDocChunks = (doc) => {
          chunkViewTab.value = 'chunks';
          filterKbId.value = doc.kb_id;
          filterDocId.value = doc.id;
          refreshChunks();
        };

        const addFaqRow = () => {
          faqForm.items.push({ standard_question: '', similar_questions_text: '', answer: '', priority: 3 });
        };

        const submitBatchFAQ = async () => {
          const payloadItems = faqForm.items.map(it => ({
            standard_question: it.standard_question,
            similar_questions: it.similar_questions_text ? it.similar_questions_text.split(/[;；\n]+/).map(s => s.trim()).filter(Boolean) : [],
            answer: it.answer,
            priority: it.priority || 3
          }));
          const res = await authFetch('/api/v1/documents/faq/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              kb_id: faqForm.kb_id,
              document_name: '结构化FAQ问答集',
              items: payloadItems
            })
          });
          if (!res.ok) return alert('批量导入失败');
          showFaqImportModal.value = false;
          await fetchKBs();
          await refreshDocAndChunks();
          alert('FAQ 录入成功！');
        };

        const openVersionModal = async (doc) => {
          selectedDoc.value = doc;
          const res = await authFetch(`/api/v1/documents/${doc.id}/versions`);
          if (res.ok) {
            docVersions.value = await res.json();
            showVersionModal.value = true;
          }
        };

        const rollbackVersion = async (targetVer) => {
          if (confirm(`确认将文档【${selectedDoc.value.name}】回滚到历史版本 v${targetVer} 吗？`)) {
            const res = await authFetch(`/api/v1/documents/${selectedDoc.value.id}/rollback?target_version=${targetVer}`, { method: 'POST' });
            if (res.ok) {
              showVersionModal.value = false;
              await fetchKBs();
              await refreshDocAndChunks();
              alert(`已成功恢复历史版本 v${targetVer}！`);
            }
          }
        };

        const deleteDoc = async (doc) => {
          if (confirm(`确认删除文档【${doc.name}】？关联切片也将一并清除。`)) {
            const res = await authFetch(`/api/v1/documents/${doc.id}`, { method: 'DELETE' });
            if (res.ok) {
              await fetchKBs();
              await refreshDocAndChunks();
            }
          }
        };

        const submitCreateSession = async () => {
          if (!newSessionForm.customer_name || !newSessionForm.customer_id) return alert('请填写客户姓名与ID');
          const res = await authFetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              customer_id: newSessionForm.customer_id,
              customer_name: newSessionForm.customer_name,
              product_code: currentProductCode.value
            })
          });
          if (res.ok) {
            const created = await res.json();
            showNewSessionModal.value = false;
            newSessionForm.customer_name = '';
            newSessionForm.customer_id = '';
            await fetchSessions();
            await switchSession(created);
          }
        };

        // ================= 4.5 BadCase 闭环治理与运营模块 API =================
        const badcaseActiveTab = ref('clusters'); // 'clusters', 'all_cases', 'thresholds'
        const badCaseClusters = ref([]);
        const selectedCluster = ref(null);
        const clusterCases = ref([]);
        const isClustering = ref(false);
        const isValidating = ref(false);

        // 全量 BadCase 池相关
        const allBadCases = ref([]);
        const allBadCasesTotal = ref(0);
        const allBadCasesPage = ref(1);
        const allBadCasesPageSize = ref(15);
        const selectedCaseIds = ref([]);
        const filterCaseStatus = ref('');
        const filterClusterStatus = ref('all');
        const filterRootCause = ref('');
        const caseSearchKeyword = ref('');

        // 阈值配置
        const selectedThresholdKbId = ref('');
        const thresholdForm = reactive({
          threshold_low: 0.30,
          threshold_high: 0.70,
          short_query_len: 5,
          candidate_rank_start: 4,
          candidate_rank_end: 10,
          context_window_rounds: 3
        });
        const thresholdAuditLogs = ref([]);
        const isSavingThreshold = ref(false);

        // 弹窗状态
        const showReviseDocModal = ref(false);
        const isSubmittingRevise = ref(false);
        const reviseDocForm = reactive({
          doc_id: '',
          doc_name: '',
          current_content: '',
          new_content: '',
          change_summary: '',
          case_id: null,
          cluster_id: null
        });

        const showManualClusterModal = ref(false);
        const isSubmittingManualCluster = ref(false);
        const manualClusterForm = reactive({
          cluster_name: '',
          standard_question: ''
        });

        const showSingleAdoptModal = ref(false);
        const isSubmittingSingleAdopt = ref(false);
        const singleAdoptForm = reactive({
          case_id: '',
          action: 'CREATE_FAQ',
          standard_question: '',
          similar_questions_text: '',
          answer: '',
          target_doc_id: ''
        });

        const showSingleRejectModal = ref(false);
        const singleRejectForm = reactive({
          case_id: '',
          reject_reason: '业务不支持或无效提问'
        });
        const filterBadCaseKbId = ref(assignedKbId.value || '');
        const filterBadCaseStatus = ref('');
        const filterBadCaseScene = ref('');
        const badCaseSearch = ref('');
        const dashboardStats = ref({
          total_cases_collected: 0,
          total_clusters: 0,
          pending_clusters: 0,
          adopted_clusters: 0,
          average_pass_rate: 85.0,
          case_types: { user_feedback: 0, low_confidence: 0, agent_label: 0 }
        });

        // 弹窗状态
        const showAdoptModal = ref(false);
        const isSubmittingAdopt = ref(false);
        const adoptForm = reactive({
          action: 'CREATE_FAQ',
          standard_question: '',
          similar_questions_text: '',
          answer: '',
          target_doc_id: ''
        });

        const showLinkModal = ref(false);
        const linkForm = reactive({
          target_doc_id: '',
          notes: ''
        });

        const showRejectModal = ref(false);
        const rejectForm = reactive({
          reason_select: '闲聊或非业务支持类提问',
          reject_reason: ''
        });

        const showValidationModal = ref(false);
        const validationReport = ref({
          cluster_name: '',
          pass_rate: 0,
          items: []
        });

        const showFeedbackModal = ref(false);
        const activeFeedbackMessage = ref(null);
        const feedbackForm = reactive({
          selectedReason: '答非所问',
          comment: ''
        });

        const showAgentLabelModal = ref(false);
        const activeAgentLabelMessage = ref(null);
        const agentLabelForm = reactive({
          label_category: 'WRONG_ANSWER',
          notes: ''
        });

        const showAnalyticsModal = ref(false);

        const filteredClusters = computed(() => {
          let list = badCaseClusters.value || [];
          if (filterBadCaseScene.value) {
            list = list.filter(c => c.recommended_action === filterBadCaseScene.value);
          }
          if (badCaseSearch.value && badCaseSearch.value.trim()) {
            const kw = badCaseSearch.value.trim().toLowerCase();
            list = list.filter(c => 
              (c.representative_query || '').toLowerCase().includes(kw) ||
              (c.cluster_name || '').toLowerCase().includes(kw)
            );
          }
          return list;
        });

        const fetchBadCasesAndClusters = async () => {
          if (!hasMenuPermission('badcases')) return;
          try {
            let url = '/api/v1/badcases/clusters?';
            if (filterBadCaseKbId.value) url += `kb_id=${filterBadCaseKbId.value}&`;
            if (filterBadCaseStatus.value) url += `status=${filterBadCaseStatus.value}&`;
            const res = await authFetch(url);
            if (res.ok) {
              badCaseClusters.value = await res.json();
              if (selectedCluster.value) {
                const refreshed = badCaseClusters.value.find(c => c.id === selectedCluster.value.id);
                if (refreshed) {
                  selectedCluster.value = refreshed;
                } else if (badCaseClusters.value.length > 0) {
                  selectCluster(badCaseClusters.value[0]);
                }
              } else if (badCaseClusters.value.length > 0) {
                selectCluster(badCaseClusters.value[0]);
              }
            }

            // 拉取全景报表指标
            let dashUrl = '/api/v1/badcases/analytics/dashboard';
            if (filterBadCaseKbId.value) dashUrl += `?kb_id=${filterBadCaseKbId.value}`;
            const dashRes = await authFetch(dashUrl);
            if (dashRes.ok) {
              const dashData = await dashRes.json();
              dashboardStats.value = {
                ...dashData.summary,
                case_types: dashData.case_type_breakdown
              };
            }
          } catch (e) {
            console.error('拉取BadCase数据失败', e);
          }
        };

        const selectCluster = async (c) => {
          selectedCluster.value = c;
          await fetchClusterCases(c.id);
        };

        const fetchClusterCases = async (clusterId) => {
          try {
            const res = await authFetch(`/api/v1/badcases/clusters/${clusterId}/cases`);
            if (res.ok) {
              const data = await res.json();
              clusterCases.value = data.cases || [];
              if (data.cluster) {
                selectedCluster.value = data.cluster;
              }
            }
          } catch (e) {
            console.error('获取簇详情失败', e);
          }
        };

        const triggerClustering = async () => {
          isClustering.value = true;
          try {
            let url = '/api/v1/badcases/cluster/run';
            if (filterBadCaseKbId.value) url += `?kb_id=${filterBadCaseKbId.value}`;
            const res = await authFetch(url, { method: 'POST' });
            if (res.ok) {
              const data = await res.json();
              alert(data.message || '聚类完成');
              await fetchBadCasesAndClusters();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '聚类失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isClustering.value = false;
          }
        };

        const onAdoptActionChange = () => {
          if (adoptForm.action === 'CREATE_FAQ') {
            adoptForm.standard_question = selectedCluster.value?.cluster_name || '';
          } else if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            if (adoptForm.target_doc_id && documents.value) {
              const d = documents.value.find(doc => doc.id === adoptForm.target_doc_id);
              if (d) adoptForm.standard_question = d.name.replace(/\.(faq|md)$/i, '');
            } else if (selectedCluster.value?.target_knowledge_title) {
              adoptForm.standard_question = selectedCluster.value.target_knowledge_title.replace(/\.(faq|md)$/i, '');
            }
          }
        };

        const onAdoptTargetDocChange = () => {
          if (adoptForm.action === 'ADD_SIMILAR_QUERY' && adoptForm.target_doc_id && documents.value) {
            const d = documents.value.find(doc => doc.id === adoptForm.target_doc_id);
            if (d) adoptForm.standard_question = d.name.replace(/\.(faq|md)$/i, '');
          }
        };

        const openAdoptModal = async (c) => {
          selectedCluster.value = c;
          adoptForm.action = c.recommended_action === 'ADD_SIMILAR_QUERY' ? 'ADD_SIMILAR_QUERY' : 'CREATE_FAQ';
          adoptForm.similar_questions_text = (c.sample_queries || []).join('\n');
          adoptForm.target_doc_id = c.target_knowledge_id || '';
          adoptForm.answer = '';

          if (!documents.value || documents.value.length === 0) {
            try {
              const res = await authFetch('/api/v1/documents?page=1&page_size=200');
              if (res.ok) documents.value = await res.json();
            } catch (e) {}
          }

          if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            if (adoptForm.target_doc_id && documents.value) {
              const d = documents.value.find(doc => doc.id === adoptForm.target_doc_id);
              if (d) {
                adoptForm.standard_question = d.name.replace(/\.(faq|md)$/i, '');
              } else {
                adoptForm.standard_question = c.target_knowledge_title ? c.target_knowledge_title.replace(/\.(faq|md)$/i, '') : (c.cluster_name || '');
              }
            } else if (c.target_knowledge_title) {
              adoptForm.standard_question = c.target_knowledge_title.replace(/\.(faq|md)$/i, '');
            } else {
              adoptForm.standard_question = c.cluster_name || '';
            }
          } else {
            adoptForm.standard_question = c.cluster_name || '';
          }

          showAdoptModal.value = true;
        };

        const submitAdoptCluster = async () => {
          if (!adoptForm.standard_question.trim()) {
            alert('请输入标准问题');
            return;
          }
          if (!adoptForm.answer.trim()) {
            alert('请输入解答内容');
            return;
          }
          isSubmittingAdopt.value = true;
          try {
            const rawSim = adoptForm.similar_questions_text.split(/[\n；;]/).map(s => s.trim()).filter(Boolean);
            const res = await authFetch(`/api/v1/badcases/clusters/${selectedCluster.value.id}/adopt`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                action: adoptForm.action,
                standard_question: adoptForm.standard_question.trim(),
                similar_questions: rawSim,
                answer: adoptForm.answer.trim(),
                target_doc_id: adoptForm.target_doc_id || null
              })
            });
            if (res.ok) {
              const data = await res.json();
              alert(data.message || '采纳成功');
              showAdoptModal.value = false;
              await fetchBadCasesAndClusters();
              if (selectedCluster.value) {
                await fetchClusterCases(selectedCluster.value.id);
              }
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '采纳失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isSubmittingAdopt.value = false;
          }
        };

        const openLinkModal = (c) => {
          selectedCluster.value = c;
          linkForm.target_doc_id = '';
          linkForm.notes = '';
          showLinkModal.value = true;
        };

        const submitLinkCluster = async () => {
          if (!linkForm.target_doc_id) {
            alert('请选择要关联的目标文档');
            return;
          }
          try {
            const res = await authFetch(`/api/v1/badcases/clusters/${selectedCluster.value.id}/link`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                target_doc_id: linkForm.target_doc_id,
                notes: linkForm.notes
              })
            });
            if (res.ok) {
              showLinkModal.value = false;
              alert('已关联至已有知识');
              await fetchBadCasesAndClusters();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '关联失败');
            }
          } catch (e) {
            alert('网络异常');
          }
        };

        const openRejectModal = (c) => {
          selectedCluster.value = c;
          rejectForm.reason_select = '闲聊或非业务支持类提问';
          rejectForm.reject_reason = '闲聊或非业务支持类提问';
          showRejectModal.value = true;
        };

        const submitRejectCluster = async () => {
          const reason = rejectForm.reason_select === 'OTHER' ? rejectForm.reject_reason : (rejectForm.reject_reason || rejectForm.reason_select);
          if (!reason.trim()) {
            alert('请输入驳回原因');
            return;
          }
          try {
            const res = await authFetch(`/api/v1/badcases/clusters/${selectedCluster.value.id}/reject`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ reject_reason: reason })
            });
            if (res.ok) {
              showRejectModal.value = false;
              alert('已驳回该簇');
              await fetchBadCasesAndClusters();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '驳回失败');
            }
          } catch (e) {
            alert('网络异常');
          }
        };

        const runRegressionValidation = async (c) => {
          isValidating.value = true;
          try {
            const res = await authFetch(`/api/v1/badcases/clusters/${c.id}/validate`, {
              method: 'POST'
            });
            if (res.ok) {
              const data = await res.json();
              validationReport.value = data.data || {};
              showValidationModal.value = true;
              await fetchBadCasesAndClusters();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '回流验证失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isValidating.value = false;
          }
        };

        const handleThumbUp = async (msg) => {
          msg.user_rated = 'UP';
          try {
            await authFetch('/api/v1/badcases/feedback', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message_id: msg.id,
                session_id: currentSession.value.id,
                feedback_type: 'UP'
              })
            });
            alert('感谢您的好评与肯定！');
          } catch (e) {}
        };

        const openFeedbackModal = (msg) => {
          activeFeedbackMessage.value = msg;
          feedbackForm.selectedReason = '答非所问';
          feedbackForm.comment = '';
          showFeedbackModal.value = true;
        };

        const submitUserFeedback = async () => {
          if (!activeFeedbackMessage.value || !currentSession.value) return;
          try {
            const comment = `${feedbackForm.selectedReason}${feedbackForm.comment ? ': ' + feedbackForm.comment : ''}`;
            const res = await authFetch('/api/v1/badcases/feedback', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message_id: activeFeedbackMessage.value.id,
                session_id: currentSession.value.id,
                feedback_type: 'DOWN',
                comment: comment
              })
            });
            if (res.ok) {
              activeFeedbackMessage.value.user_rated = 'DOWN';
              showFeedbackModal.value = false;
              alert('感谢您的反馈！该问题已实时沉淀至BadCase优化池。');
            }
          } catch (e) {
            alert('提交失败');
          }
        };

        const openAgentLabelModal = (msg) => {
          activeAgentLabelMessage.value = msg;
          agentLabelForm.label_category = 'WRONG_ANSWER';
          agentLabelForm.notes = '';
          showAgentLabelModal.value = true;
        };

        const submitAgentLabel = async () => {
          if (!activeAgentLabelMessage.value || !currentSession.value) return;
          try {
            const res = await authFetch('/api/v1/badcases/agent-label', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message_id: activeAgentLabelMessage.value.id,
                session_id: currentSession.value.id,
                label_category: agentLabelForm.label_category,
                notes: agentLabelForm.notes
              })
            });
            if (res.ok) {
              showAgentLabelModal.value = false;
              alert('坐席质检标错成功，已入库BadCase优化池');
            }
          } catch (e) {
            alert('标注失败');
          }
        };

        const openAnalyticsDashboard = async () => {
          await fetchBadCasesAndClusters();
          showAnalyticsModal.value = true;
        };

        const getActionDisplay = (action) => {
          const map = {
            'ADD_SIMILAR_QUERY': '场景 A: 追加相似问法 (知识已有但长尾召回率低)',
            'CREATE_FAQ': '场景 B: 新建独立 FAQ (纯业务盲区)',
            'UPDATE_DOC': '场景 C: 修订长文本知识库 (内容错误或细则缺失)',
            'TUNE_KNOWLEDGE': '场景 D: 知识调优与负向排除 (匹配混淆)',
            'OPTIMIZE_CONTEXT': '场景 E: 优化多轮指代策略 (上下文缺失)',
            'CLARIFY_PROMPT': '场景 F: 配置反问澄清话术 (用户问题模糊)',
            'REJECT_CLUSTER': '场景 G: 整簇驳回 / 敏感词加黑 (无效 case)'
          };
          return map[action] || action;
        };

        // 全量 BadCase 池拉取
        const fetchAllBadCasesList = async () => {
          try {
            const kb = filterBadCaseKbId.value || assignedKbId.value || '';
            const url = `/api/v1/badcases/list?page=${allBadCasesPage.value}&page_size=${allBadCasesPageSize.value}` +
              (kb ? `&kb_id=${kb}` : '') +
              (filterCaseStatus.value ? `&status=${filterCaseStatus.value}` : '') +
              (filterClusterStatus.value ? `&cluster_status=${filterClusterStatus.value}` : '') +
              (filterRootCause.value ? `&root_cause_code=${filterRootCause.value}` : '') +
              (caseSearchKeyword.value ? `&keyword=${encodeURIComponent(caseSearchKeyword.value)}` : '');
            
            const res = await authFetch(url);
            if (res.ok) {
              const data = await res.json();
              allBadCases.value = data.items || [];
              allBadCasesTotal.value = data.total || 0;
            }
          } catch (e) {
            console.error('拉取全量BadCase失败', e);
          }
        };

        const toggleSelectCase = (id) => {
          const idx = selectedCaseIds.value.indexOf(id);
          if (idx > -1) {
            selectedCaseIds.value.splice(idx, 1);
          } else {
            selectedCaseIds.value.push(id);
          }
        };

        const toggleSelectAllCases = () => {
          if (selectedCaseIds.value.length === allBadCases.value.length) {
            selectedCaseIds.value = [];
          } else {
            selectedCaseIds.value = allBadCases.value.map(c => c.id);
          }
        };

        const openManualClusterModal = () => {
          if (selectedCaseIds.value.length === 0) {
            alert('请先勾选需要合并建簇的 BadCase');
            return;
          }
          manualClusterForm.cluster_name = '';
          manualClusterForm.standard_question = '';
          showManualClusterModal.value = true;
        };

        const submitManualCluster = async () => {
          if (!manualClusterForm.cluster_name.trim()) {
            alert('请输入簇名称或代表问句');
            return;
          }
          isSubmittingManualCluster.value = true;
          try {
            const res = await authFetch('/api/v1/badcases/manual-cluster', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                case_ids: selectedCaseIds.value,
                cluster_name: manualClusterForm.cluster_name.trim(),
                standard_question: manualClusterForm.standard_question.trim() || null
              })
            });
            if (res.ok) {
              alert('手动合并建簇成功！已加入高频问题簇看板');
              showManualClusterModal.value = false;
              selectedCaseIds.value = [];
              await fetchBadCasesAndClusters();
              await fetchAllBadCasesList();
              badcaseActiveTab.value = 'clusters';
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '合并失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isSubmittingManualCluster.value = false;
          }
        };

        // 修订长文本知识库草稿 (场景 C)
        const openReviseDocModal = async (docId, docName, caseId = null, clusterId = null) => {
          reviseDocForm.doc_id = docId;
          reviseDocForm.doc_name = docName;
          reviseDocForm.case_id = caseId;
          reviseDocForm.cluster_id = clusterId;
          reviseDocForm.change_summary = '';
          reviseDocForm.new_content = '正在载入当前文档内容...';
          showReviseDocModal.value = true;

          try {
            const res = await authFetch(`/api/v1/documents/${docId}`);
            if (res.ok) {
              const docData = await res.json();
              reviseDocForm.new_content = docData.content || '';
            }
          } catch (e) {
            reviseDocForm.new_content = '';
          }
        };

        const submitReviseDoc = async () => {
          if (!reviseDocForm.change_summary.trim()) {
            alert('请输入修订说明');
            return;
          }
          if (!reviseDocForm.new_content.trim()) {
            alert('文档正文不能为空');
            return;
          }
          isSubmittingRevise.value = true;
          try {
            const res = await authFetch('/api/v1/badcases/revise-doc', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                doc_id: reviseDocForm.doc_id,
                new_content: reviseDocForm.new_content,
                change_summary: reviseDocForm.change_summary,
                case_id: reviseDocForm.case_id,
                cluster_id: reviseDocForm.cluster_id
              })
            });
            if (res.ok) {
              alert('已成功发起修订版本草稿，文档状态置为待审核 (PENDING_REVIEW)');
              showReviseDocModal.value = false;
              await fetchBadCasesAndClusters();
              await fetchAllBadCasesList();
              await refreshDocAndChunks();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '修订失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isSubmittingRevise.value = false;
          }
        };

        // 单条采纳与驳回
        const openSingleAdoptModal = (c) => {
          singleAdoptForm.case_id = c.id;
          singleAdoptForm.action = 'CREATE_FAQ';
          singleAdoptForm.standard_question = c.user_query;
          singleAdoptForm.similar_questions_text = c.user_query;
          singleAdoptForm.answer = '';
          singleAdoptForm.target_doc_id = (c.recall_sources && c.recall_sources[0]) ? c.recall_sources[0].doc_id : '';
          showSingleAdoptModal.value = true;
        };

        const submitSingleAdopt = async () => {
          if (!singleAdoptForm.standard_question.trim()) {
            alert('请输入标准问题');
            return;
          }
          if (!singleAdoptForm.answer.trim()) {
            alert('请输入解答');
            return;
          }
          isSubmittingSingleAdopt.value = true;
          try {
            const rawSim = (singleAdoptForm.similar_questions_text || '').split(/[;\n；]/).map(s => s.trim()).filter(Boolean);
            const res = await authFetch(`/api/v1/badcases/${singleAdoptForm.case_id}/adopt`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                action: singleAdoptForm.action,
                standard_question: singleAdoptForm.standard_question.trim(),
                similar_questions: rawSim,
                answer: singleAdoptForm.answer.trim(),
                target_doc_id: singleAdoptForm.target_doc_id || null
              })
            });
            if (res.ok) {
              alert('单条 BadCase 采纳成功并提交审核');
              showSingleAdoptModal.value = false;
              await fetchAllBadCasesList();
              await fetchBadCasesAndClusters();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '采纳失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isSubmittingSingleAdopt.value = false;
          }
        };

        const openSingleRejectModal = (c) => {
          singleRejectForm.case_id = c.id;
          singleRejectForm.reject_reason = '业务不支持或无效提问';
          showSingleRejectModal.value = true;
        };

        const submitSingleReject = async () => {
          try {
            const res = await authFetch(`/api/v1/badcases/${singleRejectForm.case_id}/reject`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ reject_reason: singleRejectForm.reject_reason })
            });
            if (res.ok) {
              alert('该 Case 已驳回');
              showSingleRejectModal.value = false;
              await fetchAllBadCasesList();
              await fetchBadCasesAndClusters();
            }
          } catch (e) {
            alert('网络异常');
          }
        };

        // 阈值配置
        const fetchThresholdConfigs = async () => {
          try {
            if (!selectedThresholdKbId.value && kbs.value.length > 0) {
              selectedThresholdKbId.value = kbs.value[0].id;
            }
            await onThresholdKbChange();
            await fetchThresholdLogs();
          } catch (e) {}
        };

        const onThresholdKbChange = async () => {
          if (!selectedThresholdKbId.value) return;
          try {
            const res = await authFetch('/api/v1/badcases/configs');
            if (res.ok) {
              const list = await res.json();
              const found = list.find(c => c.kb_id === selectedThresholdKbId.value);
              if (found) {
                thresholdForm.threshold_low = found.threshold_low;
                thresholdForm.threshold_high = found.threshold_high;
                thresholdForm.short_query_len = found.short_query_len;
                thresholdForm.candidate_rank_start = found.candidate_rank_start;
                thresholdForm.candidate_rank_end = found.candidate_rank_end;
                thresholdForm.context_window_rounds = found.context_window_rounds;
              } else {
                thresholdForm.threshold_low = 0.30;
                thresholdForm.threshold_high = 0.70;
                thresholdForm.short_query_len = 5;
                thresholdForm.candidate_rank_start = 4;
                thresholdForm.candidate_rank_end = 10;
                thresholdForm.context_window_rounds = 3;
              }
            }
          } catch (e) {}
        };

        const submitThresholdConfig = async () => {
          if (!selectedThresholdKbId.value) {
            alert('请选择目标知识库');
            return;
          }
          isSavingThreshold.value = true;
          try {
            const res = await authFetch(`/api/v1/badcases/configs/${selectedThresholdKbId.value}`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(thresholdForm)
            });
            if (res.ok) {
              alert('阈值配置已保存并记入审计日志');
              await fetchThresholdLogs();
            } else {
              const err = await res.json().catch(() => ({}));
              alert(err.detail || '保存失败');
            }
          } catch (e) {
            alert('网络异常');
          } finally {
            isSavingThreshold.value = false;
          }
        };

        const fetchThresholdLogs = async () => {
          try {
            const res = await authFetch(`/api/v1/badcases/configs/logs?kb_id=${selectedThresholdKbId.value || ''}`);
            if (res.ok) {
              thresholdAuditLogs.value = await res.json();
            }
          } catch (e) {}
        };

        // ================= 5. 认证与登录退出 =================

        const handleLoginSubmit = async () => {
          if (!loginForm.username || !loginForm.password) {
            loginError.value = '请输入登录账号与密码';
            return;
          }
          loginLoading.value = true;
          loginError.value = '';
          try {
            const res = await fetch('/api/v1/auth/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                username: loginForm.username,
                password: loginForm.password
              })
            });
            if (res.ok) {
              const data = await res.json();
              currentRole.value = data.role;
              currentUserId.value = data.user_id;
              currentUsername.value = data.username;
              currentUserDisplayName.value = data.display_name;
              currentUserProduct.value = data.product_code || (data.role === 'tech_agent' ? 'SAAS_CLOUD' : '');
              if (currentUserProduct.value) {
                currentProductCode.value = currentUserProduct.value;
              }
              isLoggedIn.value = true;
              localStorage.setItem('smart_cs_user', JSON.stringify(data));

              // 角色初始化
              if (data.role === 'user') {
                activeMenu.value = 'chat';
                await initCustomerNewSession(true);
              } else if (data.role === 'operator') {
                activeMenu.value = 'badcases';
                assignedKbId.value = data.assigned_kb_id || '';
                filterKbId.value = data.assigned_kb_id || '';
                filterBadCaseKbId.value = data.assigned_kb_id || '';
                await fetchKBs();
                await refreshDocAndChunks();
                await fetchBadCasesAndClusters();
              } else {
                activeMenu.value = 'chat';
                await fetchKBs();
                await fetchSessions();
                if (hasMenuPermission('chunks')) {
                  await refreshDocAndChunks();
                }
              }
              startPolling();
            } else {
              const err = await res.json().catch(() => ({}));
              loginError.value = err.detail || '账号或密码错误';
            }
          } catch (e) {
            loginError.value = '网络异常，请重试';
          } finally {
            loginLoading.value = false;
          }
        };

        const quickFillLogin = (u, p) => {
          loginForm.username = u;
          loginForm.password = p;
          handleLoginSubmit();
        };

        const handleLogout = () => {
          localStorage.removeItem('smart_cs_user');
          isLoggedIn.value = false;
          stopPolling();
          currentSession.value = null;
          messageList.value = [];
          loginForm.username = '';
          loginForm.password = '';
        };

        // 窗口关闭/离开时自动挂断（若在人工接待模式）
        window.addEventListener('beforeunload', () => {
          if (isLoggedIn.value && currentRole.value === 'user' && currentSession.value && currentSession.value.status === 'HUMAN_CONNECTED') {
            navigator.sendBeacon(`/api/v1/chat/hangup?session_id=${currentSession.value.id}`);
          }
        });

        // 挂载执行
        onMounted(async () => {
          if (isLoggedIn.value) {
            if (currentRole.value === 'user') {
              activeMenu.value = 'chat';
              await initCustomerNewSession(true);
            } else if (currentRole.value === 'operator') {
              activeMenu.value = 'badcases';
              filterKbId.value = assignedKbId.value || '';
              filterBadCaseKbId.value = assignedKbId.value || '';
              await fetchKBs();
              await refreshDocAndChunks();
              await fetchBadCasesAndClusters();
            } else {
              await fetchKBs();
              await fetchSessions();
              if (hasMenuPermission('chunks')) {
                await refreshDocAndChunks();
              }
            }
            startPolling();
          }
        });

        return {
          isLoggedIn,
          loginForm,
          loginError,
          loginLoading,
          currentUserDisplayName,
          currentUsername,
          currentUserProduct,
          currentRole,
          currentUserId,
          roleLabel,
          hasMenuPermission,
          canManageHumanSession,
          activeMenu,
          currentProductCode,
          sessions,
          filteredSessions,
          sessionFilterStatus,
          currentSession,
          messageList,
          inputQuery,
          isThinking,
          chatContainer,
          inspectingSource,
          newAssignmentAlert,
          handleJumpToAssignedSession,
          kbs,
          chunkViewTab,
          documents,
          chunkList,
          filterKbId,
          filterDocType,
          filterDocStatus,
          filterDocId,
          searchKeyword,
          getKbName,
          showUploadDocModal,
          uploadDocTab,
          isSubmittingDoc,
          selectedFileName,
          fileInput,
          newDoc,
          openUploadModal,
          onFileSelected,
          submitCreateDoc,
          showNewSessionModal,
          newSessionForm,
          submitCreateSession,
          showCreateKBDocModal,
          newKB,
          submitCreateKB,
          showConfigModal,
          editingKB,
          kbConfigForm,
          openConfigModal,
          saveKBConfig,
          showEditKBModal,
          editKBForm,
          openEditKBModal,
          saveKBBasicInfo,
          showFaqImportModal,
          faqForm,
          addFaqRow,
          submitBatchFAQ,
          showVersionModal,
          selectedDoc,
          docVersions,
          openVersionModal,
          rollbackVersion,
          showPreviewDocModal,
          previewDocData,
          openPreviewDoc,
          showEditDocModal,
          editDocForm,
          openEditDocModal,
          submitSaveDocEdit,
          viewDocChunks,
          deleteDoc,
          approveDoc,
          rejectDoc,
          confirmDeleteKB,
          toggleKBStatus,
          onFilterKbChange,
          onFilterDocChange,
          refreshDocs,
          refreshChunks,
          refreshDocAndChunks,
          handleSearch,
          switchSession,
          handleSend,
          sendQuickPrompt,
          handleManualTransferHuman,
          handleUserHangup,
          finishHumanService,
          openSourceDrawer,
          onUserProductChange,
          handleLoginSubmit,
          quickFillLogin,
          handleLogout,
          assignedKbId,
          assignedKbName,
          getKbNameById,
          badCaseClusters,
          selectedCluster,
          clusterCases,
          isClustering,
          isValidating,
          filterBadCaseKbId,
          filterBadCaseStatus,
          filterBadCaseScene,
          badCaseSearch,
          dashboardStats,
          filteredClusters,
          showAdoptModal,
          isSubmittingAdopt,
          adoptForm,
          showLinkModal,
          linkForm,
          showRejectModal,
          rejectForm,
          showValidationModal,
          validationReport,
          showFeedbackModal,
          feedbackForm,
          showAgentLabelModal,
          agentLabelForm,
          showAnalyticsModal,
          fetchBadCasesAndClusters,
          selectCluster,
          fetchClusterCases,
          triggerClustering,
          openAdoptModal,
          submitAdoptCluster,
          openLinkModal,
          submitLinkCluster,
          openRejectModal,
          submitRejectCluster,
          runRegressionValidation,
          handleThumbUp,
          openFeedbackModal,
          submitUserFeedback,
          openAgentLabelModal,
          submitAgentLabel,
          openAnalyticsDashboard,
          badcaseActiveTab,
          allBadCases,
          allBadCasesTotal,
          allBadCasesPage,
          allBadCasesPageSize,
          selectedCaseIds,
          filterCaseStatus,
          filterClusterStatus,
          filterRootCause,
          caseSearchKeyword,
          fetchAllBadCasesList,
          toggleSelectCase,
          toggleSelectAllCases,
          showManualClusterModal,
          isSubmittingManualCluster,
          manualClusterForm,
          openManualClusterModal,
          submitManualCluster,
          showReviseDocModal,
          isSubmittingRevise,
          reviseDocForm,
          openReviseDocModal,
          submitReviseDoc,
          showSingleAdoptModal,
          isSubmittingSingleAdopt,
          singleAdoptForm,
          openSingleAdoptModal,
          submitSingleAdopt,
          showSingleRejectModal,
          singleRejectForm,
          openSingleRejectModal,
          submitSingleReject,
          selectedThresholdKbId,
          thresholdForm,
          thresholdAuditLogs,
          isSavingThreshold,
          fetchThresholdConfigs,
          onThresholdKbChange,
          submitThresholdConfig,
          fetchThresholdLogs,
          getActionDisplay
        };
      }
    }).mount('#app');
  </script>
</body>
</html>
