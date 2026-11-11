import os
import re

with open("scripts/legacy/patches/build_frontend.py", "r", encoding="utf-8") as f:
    content = f.read()

# ================= 1. 在 BadCase 工作台顶部加入 3 大子 Tab 导航 =================
old_toolbar = '''          <!-- 知识库与状态筛选工具栏 -->
          <div class="bg-white p-4 rounded-2xl border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">'''

new_tabs_and_toolbar = '''          <!-- 子 Tab 导航栏：问题簇 / 全量池与长尾 / 判定阈值配置 -->
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
            <div class="bg-white p-4 rounded-2xl border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">'''

if old_toolbar in content:
    content = content.replace(old_toolbar, new_tabs_and_toolbar, 1)
    print("Tab 1 & navigation added successfully.")
else:
    print("Warning: old_toolbar not found!")

# ================= 2. 在左侧问题簇项中增加 7 大根因定位标签 =================
old_cluster_badge = '''                  <!-- 场景与状态标签 -->
                  <div class="flex flex-wrap items-center gap-1.5 text-[10px]">'''

new_cluster_badge = '''                  <!-- 根因与场景状态标签 -->
                  <div class="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <!-- 7 大根因标签 -->
                    <span v-if="c.root_cause_name" class="bg-indigo-100 text-indigo-800 border border-indigo-200 px-2 py-0.5 rounded-md font-bold">
                      🎯 {{ c.root_cause_name }}
                    </span>'''

if old_cluster_badge in content:
    content = content.replace(old_cluster_badge, new_cluster_badge, 1)
    print("Cluster root cause badge added successfully.")

# ================= 3. 在右侧问题簇详情的 AI 智能诊断决策卡片中加入根因与定义 =================
old_ai_card = '''                    <div class="text-xs text-slate-700 space-y-1 leading-relaxed">
                      <p><strong>推荐动作:</strong> 
                        <span class="font-bold text-indigo-700">
                          {{ selectedCluster.recommended_action === 'ADD_SIMILAR_QUERY' ? '场景 A: 追加相似问 (已有该知识但在长尾问法上召回率低)' : (selectedCluster.recommended_action === 'NEW_FAQ' ? '场景 B: 新建独立 FAQ (业务盲区/新业务规则缺失)' : '场景 C: 修订长文本知识库') }}
                        </span>
                      </p>
                      <p><strong>诊断依据:</strong> {{ selectedCluster.recommendation_reason || '根据近期多位用户针对同类问题的差评反馈与检索切片置信度聚类生成' }}</p>'''

new_ai_card = '''                    <div class="text-xs text-slate-700 space-y-2 leading-relaxed">
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
                      <p><strong>诊断依据:</strong> {{ selectedCluster.recommended_reason || '根据近期多位用户针对同类问题的差评反馈与检索切片置信度聚类生成' }}</p>'''

if old_ai_card in content:
    content = content.replace(old_ai_card, new_ai_card, 1)
    print("AI recommendation card updated with root cause.")

# ================= 4. 在右侧问题簇详情按钮栏加入【📝 修订原文档】 =================
old_cluster_buttons = '''                    <button 
                      @click="openLinkModal(selectedCluster)"'''

new_cluster_buttons = '''                    <button 
                      v-if="selectedCluster.target_knowledge_id"
                      @click="openReviseDocModal(selectedCluster.target_knowledge_id, selectedCluster.target_knowledge_title || '关联文档', null, selectedCluster.id)"
                      class="bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 text-xs font-semibold px-2.5 py-1.5 rounded-xl transition cursor-pointer flex items-center gap-1"
                    >
                      <span>📝</span>
                      <span>修订原文档</span>
                    </button>
                    <button 
                      @click="openLinkModal(selectedCluster)"'''

if old_cluster_buttons in content:
    content = content.replace(old_cluster_buttons, new_cluster_buttons, 1)
    print("Revise doc button added to cluster header.")

# ================= 5. 在 clusterCases 列表项中渲染命中知识来源胶囊与单条根因 =================
old_case_item = '''                        <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 space-y-1">
                          <p class="font-semibold text-slate-900"><strong>用户提问:</strong> {{ item.user_query }}</p>
                          <p class="text-slate-600 line-clamp-2"><strong>AI回答:</strong> {{ item.ai_raw_response }}</p>
                          <p class="text-[10px] text-slate-400 font-mono">置信得分: {{ ((item.confidence_score || 0) * 100).toFixed(0) }}%</p>
                        </div>'''

new_case_item = '''                        <div class="bg-slate-50 p-2.5 rounded-lg border border-slate-100 space-y-1.5">
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
                        </div>'''

if old_case_item in content:
    content = content.replace(old_case_item, new_case_item, 1)
    print("Cluster case item updated with hit doc and root cause.")

# ================= 6. 插入 Tab 2 (全量池) 与 Tab 3 (阈值配置) HTML =================
old_tab_close = '''            </div>

          </div>
        </section>'''

new_tab_2_and_3 = '''            </div>

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
          </div>
        </section>'''

if old_tab_close in content:
    content = content.replace(old_tab_close, new_tab_2_and_3, 1)
    print("Tab 2 and Tab 3 HTML added successfully.")

# ================= 7. 增加新模态框 (修订文档、手动建簇、单条采纳、单条驳回) =================
old_modals_end = '''    <!-- ================= 模态弹窗与抽屉 ================= -->'''

new_modals = '''    <!-- ================= 模态弹窗与抽屉 ================= -->

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
    </div>'''

if old_modals_end in content:
    content = content.replace(old_modals_end, new_modals, 1)
    print("New modals added successfully.")

# ================= 8. 在 Vue setup 状态中加入新状态与新函数 =================
old_vue_states = '''        // ================= 4.5 BadCase 闭环治理与运营模块 API =================
        const badCaseClusters = ref([]);
        const selectedCluster = ref(null);
        const clusterCases = ref([]);
        const isClustering = ref(false);
        const isValidating = ref(false);'''

new_vue_states = '''        // ================= 4.5 BadCase 闭环治理与运营模块 API =================
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
        });'''

if old_vue_states in content:
    content = content.replace(old_vue_states, new_vue_states, 1)
    print("New Vue states added successfully.")

# ================= 9. 增加新函数实现 (全量池拉取、手动建簇、修订文档、阈值配置等) =================
old_func_anchor = '''        const openAnalyticsDashboard = async () => {
          await fetchBadCasesAndClusters();
          showAnalyticsModal.value = true;
        };'''

new_functions = '''        const openAnalyticsDashboard = async () => {
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
            const rawSim = singleAdoptForm.similar_questions_text.split(/[\n；;]/).map(s => s.trim()).filter(Boolean);
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
        };'''

if old_func_anchor in content:
    content = content.replace(old_func_anchor, new_functions, 1)
    print("New Vue functions added successfully.")

# ================= 10. 将新变量与新函数加入 return 对象 =================
old_return = '''          handleThumbUp,
          openFeedbackModal,
          submitUserFeedback,
          openAgentLabelModal,
          submitAgentLabel,
          openAnalyticsDashboard
        };'''

new_return = '''          handleThumbUp,
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
        };'''

if old_return in content:
    content = content.replace(old_return, new_return, 1)
    print("Vue return object updated successfully.")

with open("scripts/legacy/patches/build_frontend.py", "w", encoding="utf-8") as f:
    f.write(content)

print("scripts/legacy/patches/build_frontend.py patch complete!")
