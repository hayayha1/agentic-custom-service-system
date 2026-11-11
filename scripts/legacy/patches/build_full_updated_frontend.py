import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read original build_frontend.py
with open('scripts/legacy/patches/build_frontend.py', 'r', encoding='utf-8') as f:
    orig = f.read()

print("Original length:", len(orig))

# 1. Update quick fill login
target_login = '''          <div class="grid grid-cols-3 gap-2">
            <button 
              type="button" 
              @click="quickFillLogin('admin', 'admin123')"
              class="bg-white/5 hover:bg-white/15 border border-white/10 rounded-xl p-2.5 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👑</div>
              <div class="font-bold text-white text-[11px] mt-1">超级管理员</div>
              <div class="text-[9px] text-slate-400 font-mono">admin / admin123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('tech', 'tech123')"
              class="bg-white/5 hover:bg-white/15 border border-white/10 rounded-xl p-2.5 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👩‍💼</div>
              <div class="font-bold text-white text-[11px] mt-1">SaaS技术客服</div>
              <div class="text-[9px] text-slate-400 font-mono">tech / tech123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('user', 'user123')"
              class="bg-white/5 hover:bg-white/15 border border-white/10 rounded-xl p-2.5 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👤</div>
              <div class="font-bold text-white text-[11px] mt-1">普通用户</div>
              <div class="text-[9px] text-slate-400 font-mono">user / user123</div>
            </button>
          </div>'''

replacement_login = '''          <div class="grid grid-cols-4 gap-2">
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
              <div class="font-bold text-rose-300 text-[11px] mt-1">电商运营专员</div>
              <div class="text-[9px] text-slate-400 font-mono">ops / ops123</div>
            </button>
            <button 
              type="button" 
              @click="quickFillLogin('tech', 'tech123')"
              class="bg-white/5 hover:bg-white/15 border border-white/10 rounded-xl p-2 text-center transition group cursor-pointer"
            >
              <div class="text-base group-hover:scale-110 transition">👩‍💼</div>
              <div class="font-bold text-white text-[11px] mt-1">SaaS技术客服</div>
              <div class="text-[9px] text-slate-400 font-mono">tech / tech123</div>
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
          </div>'''

assert target_login in orig, "Failed to find target_login"
orig = orig.replace(target_login, replacement_login, 1)
print("1. Login quick fill updated.")

# 2. Update status dot in nav
target_dot = '''              <span class="w-1.5 h-1.5 rounded-full" :class="currentRole === 'admin' ? 'bg-rose-400' : (currentRole === 'tech_agent' ? 'bg-amber-400' : 'bg-emerald-400')"></span>'''
replacement_dot = '''              <span class="w-1.5 h-1.5 rounded-full" :class="currentRole === 'admin' ? 'bg-rose-400' : (currentRole === 'operator' ? 'bg-orange-400' : (currentRole === 'tech_agent' ? 'bg-amber-400' : 'bg-emerald-400'))"></span>'''
assert target_dot in orig, "Failed to find target_dot"
orig = orig.replace(target_dot, replacement_dot, 1)

# 3. Add BadCase menu item to sidebar nav
target_nav_end = '''          <!-- 菜单 3: 知识片段管理 (技术客服 与 超级管理员 可见，普通用户不可见) -->
          <button 
            v-if="hasMenuPermission('chunks')"
            @click="activeMenu = 'chunks'" 
            :class="activeMenu === 'chunks' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition duration-150 text-left cursor-pointer"
          >
            <span class="text-base">🧩</span>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span>知识片段管理</span>
                <span class="text-[9px] bg-amber-500/30 text-amber-200 px-1.5 py-0.2 rounded-full font-mono">坐席/超管</span>
              </div>
              <p class="text-[10px] opacity-75 mt-0.5 font-normal">
                {{ currentRole === 'admin' ? '文档审核/切片管理/版本回滚' : '本产品文档提交/切片查询' }}
              </p>
            </div>
          </button>
        </nav>'''

replacement_nav_end = '''          <!-- 菜单 3: 知识文档与片段治理 (运营、技术客服与超管可见) -->
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
        </nav>'''

assert target_nav_end in orig, "Failed to find target_nav_end"
orig = orig.replace(target_nav_end, replacement_nav_end, 1)
print("2. Sidebar nav badcases menu added.")

# 4. Update sidebar bottom user card
target_user_card = '''            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm"
                 :class="currentRole === 'admin' ? 'bg-rose-600 text-white' : (currentRole === 'tech_agent' ? 'bg-amber-600 text-white' : 'bg-indigo-600 text-white')">
              {{ currentRole === 'admin' ? '👑' : (currentRole === 'tech_agent' ? '👩‍💼' : '👤') }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-bold text-white truncate">{{ currentUserDisplayName }}</p>
              <p class="text-[10px] text-slate-400 font-mono truncate">
                账号: {{ currentUsername }} <span v-if="currentUserProduct" class="text-indigo-400 font-semibold">({{ currentUserProduct }})</span>
              </p>
            </div>'''

replacement_user_card = '''            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm"
                 :class="currentRole === 'admin' ? 'bg-rose-600 text-white' : (currentRole === 'operator' ? 'bg-orange-600 text-white' : (currentRole === 'tech_agent' ? 'bg-amber-600 text-white' : 'bg-indigo-600 text-white'))">
              {{ currentRole === 'admin' ? '👑' : (currentRole === 'operator' ? '🚨' : (currentRole === 'tech_agent' ? '👩‍💼' : '👤')) }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-bold text-white truncate">{{ currentUserDisplayName }}</p>
              <p class="text-[10px] text-slate-400 font-mono truncate">
                账号: {{ currentUsername }} <span v-if="currentRole === 'operator'" class="text-orange-300 font-semibold truncate">({{ assignedKbName }})</span><span v-else-if="currentUserProduct" class="text-indigo-400 font-semibold">({{ currentUserProduct }})</span>
              </p>
            </div>'''

assert target_user_card in orig, "Failed to find target_user_card"
orig = orig.replace(target_user_card, replacement_user_card, 1)
print("3. Sidebar user card updated.")

# 5. Assistant message feedback buttons (like/dislike & agent label)
target_msg_footer = '''                  <!-- 底部常驻转人工按钮 (普通用户在 AI 模式下可见，挂断后立刻可再次使用) -->'''

replacement_msg_footer = '''                  <!-- AI 回答质量评价与人工标错 (全生命周期多维采集入口) -->
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

                  <!-- 底部常驻转人工按钮 (普通用户在 AI 模式下可见，挂断后立刻可再次使用) -->'''

assert target_msg_footer in orig, "Failed to find target_msg_footer"
orig = orig.replace(target_msg_footer, replacement_msg_footer, 1)
print("4. Message feedback & agent label buttons added.")

# 6. Add Module 4: BadCase Governance Section
target_module3_end = '''          </div>
        </section>

      </main>'''

replacement_module4 = '''          </div>
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
                      {{ c.representative_query || c.cluster_name }}
                    </p>
                    <span class="flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full font-mono shadow-xs"
                          :class="c.case_count >= 3 ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-amber-100 text-amber-700 border border-amber-200'">
                      🔥 {{ c.case_count }}次进线
                    </span>
                  </div>

                  <!-- 场景与状态标签 -->
                  <div class="flex flex-wrap items-center gap-1.5 text-[10px]">
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
                        {{ selectedCluster.representative_query || selectedCluster.cluster_name }}
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

                    <div class="text-xs text-slate-700 space-y-1 leading-relaxed">
                      <p><strong>推荐动作:</strong> 
                        <span class="font-bold text-indigo-700">
                          {{ selectedCluster.recommended_action === 'ADD_SIMILAR_QUERY' ? '场景 A: 追加相似问 (已有该知识但在长尾问法上召回率低)' : (selectedCluster.recommended_action === 'NEW_FAQ' ? '场景 B: 新建独立 FAQ (业务盲区/新业务规则缺失)' : '场景 C: 修订长文本知识库') }}
                        </span>
                      </p>
                      <p><strong>诊断依据:</strong> {{ selectedCluster.recommendation_reason || '根据近期多位用户针对同类问题的差评反馈与检索切片置信度聚类生成' }}</p>
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

                        <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 space-y-1">
                          <p class="font-semibold text-slate-900"><strong>用户提问:</strong> {{ item.user_query }}</p>
                          <p class="text-slate-600 line-clamp-2"><strong>AI回答:</strong> {{ item.ai_raw_response }}</p>
                          <p class="text-[10px] text-slate-400 font-mono">置信得分: {{ ((item.confidence_score || 0) * 100).toFixed(0) }}%</p>
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
        </section>

      </main>'''

assert target_module3_end in orig, "Failed to find target_module3_end"
orig = orig.replace(target_module3_end, replacement_module4, 1)
print("5. Module 4 Badcase section added.")

# 7. Add Modals for Badcases, feedback, agent label, analytics
target_modals_end = '''    <!-- 溯源切片详情抽屉 -->
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
    </div>'''

replacement_modals = '''    <!-- 溯源切片详情抽屉 -->
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
              <tr v-for="(item, idx) in validationReport.items" :key="idx" class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-medium text-slate-900">{{ item.query }}</td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono"
                        :class="item.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'">
                    {{ item.passed ? '✅ 通过' : '❌ 未达标' }}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center font-mono font-bold"
                    :class="item.score >= 0.75 ? 'text-emerald-600' : 'text-amber-600'">
                  {{ (item.score * 100).toFixed(1) }}%
                </td>
                <td class="py-2.5 px-3 text-[11px] text-slate-500 truncate max-w-xs">
                  {{ item.matched_heading || item.doc_name || '未命中有效切片' }}
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
    </div>'''

assert target_modals_end in orig, "Failed to find target_modals_end"
orig = orig.replace(target_modals_end, replacement_modals, 1)
print("6. Modals for badcases and feedback added.")

# 8. Update Vue setup: role labels, permissions, state, methods
target_vue_init = '''        const roleLabels = {
          user: '普通客户',
          tech_agent: '技术客服',
          admin: '超级管理员'
        };
        const roleLabel = computed(() => roleLabels[currentRole.value] || '客户');

        const hasMenuPermission = (menuKey) => {
          if (menuKey === 'chat') return true;
          if (menuKey === 'chunks') return currentRole.value === 'admin' || currentRole.value === 'tech_agent';
          if (menuKey === 'kb') return currentRole.value === 'admin';
          return false;
        };'''

replacement_vue_init = '''        const assignedKbId = ref(savedUser ? (savedUser.assigned_kb_id || '') : '');

        const roleLabels = {
          user: '普通客户',
          tech_agent: '技术客服',
          admin: '超级管理员',
          operator: '知识运营'
        };
        const roleLabel = computed(() => roleLabels[currentRole.value] || '客户');

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
        };'''

assert target_vue_init in orig, "Failed to find target_vue_init"
orig = orig.replace(target_vue_init, replacement_vue_init, 1)
print("7. Vue role labels and hasMenuPermission updated.")

# 9. Add BadCase states & methods before Section 5
target_sec5 = '''        // ================= 5. 认证与登录退出 ================='''

replacement_sec5 = '''        // ================= 4.5 BadCase 闭环治理与运营模块 API =================
        const badCaseClusters = ref([]);
        const selectedCluster = ref(null);
        const clusterCases = ref([]);
        const isClustering = ref(false);
        const isValidating = ref(false);
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

        const openAdoptModal = (c) => {
          selectedCluster.value = c;
          adoptForm.action = c.recommended_action === 'ADD_SIMILAR_QUERY' ? 'ADD_SIMILAR_QUERY' : 'CREATE_FAQ';
          adoptForm.standard_question = c.suggested_standard_query || c.representative_query || '';
          adoptForm.similar_questions_text = (c.sample_queries || []).join('\\n');
          adoptForm.answer = '';
          adoptForm.target_doc_id = '';
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
            const rawSim = adoptForm.similar_questions_text.split(/[\\n；;]/).map(s => s.trim()).filter(Boolean);
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

        // ================= 5. 认证与登录退出 ================='''

assert target_sec5 in orig, "Failed to find target_sec5"
orig = orig.replace(target_sec5, replacement_sec5, 1)
print("8. Badcase states & methods added.")

# 10. Update handleLoginSubmit & onMounted for operator
target_login_role_init = '''              // 角色初始化
              if (data.role === 'user') {
                activeMenu.value = 'chat';
                await initCustomerNewSession(true);
              } else {
                activeMenu.value = 'chat';
                await fetchKBs();
                await fetchSessions();
                if (hasMenuPermission('chunks')) {
                  await refreshDocAndChunks();
                }
              }'''

replacement_login_role_init = '''              // 角色初始化
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
              }'''

assert target_login_role_init in orig, "Failed to find target_login_role_init"
orig = orig.replace(target_login_role_init, replacement_login_role_init, 1)

target_onmounted = '''        // 挂载执行
        onMounted(async () => {
          if (isLoggedIn.value) {
            if (currentRole.value === 'user') {
              activeMenu.value = 'chat';
              await initCustomerNewSession(true);
            } else {
              await fetchKBs();
              await fetchSessions();
              if (hasMenuPermission('chunks')) {
                await refreshDocAndChunks();
              }
            }
            startPolling();
          }
        });'''

replacement_onmounted = '''        // 挂载执行
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
        });'''

assert target_onmounted in orig, "Failed to find target_onmounted"
orig = orig.replace(target_onmounted, replacement_onmounted, 1)
print("9. Login & onMounted operator logic updated.")

# 11. Add new variables to return statement
target_return_end = '''          handleLoginSubmit,
          quickFillLogin,
          handleLogout
        };'''

replacement_return_end = '''          handleLoginSubmit,
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
          openAnalyticsDashboard
        };'''

assert target_return_end in orig, "Failed to find target_return_end"
orig = orig.replace(target_return_end, replacement_return_end, 1)
print("10. Return statement updated with all badcase variables.")

# Write updated build_frontend.py
with open('scripts/legacy/patches/build_frontend.py', 'w', encoding='utf-8') as f:
    f.write(orig)

print("Updated scripts/legacy/patches/build_frontend.py written successfully!")
