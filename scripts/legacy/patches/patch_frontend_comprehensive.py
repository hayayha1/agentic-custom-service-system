import os

with open('app/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Normalize \r\n to \n
html = html.replace('\r\n', '\n')

# 1. Replace Modal J (Adopt Modal)
old_modal_j = """    <!-- 弹窗 J: 采纳 BadCase 簇生成知识草稿 (进入待审核流) -->
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
                <input type="radio" v-model="adoptForm.action" value="CREATE_FAQ" @change="onAdoptActionChange" class="text-indigo-600" />
                <span>新建结构化 FAQ (推荐)</span>
              </label>
              <label class="flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer" :class="adoptForm.action === 'ADD_SIMILAR_QUERY' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold' : 'border-slate-200 text-slate-600'">
                <input type="radio" v-model="adoptForm.action" value="ADD_SIMILAR_QUERY" @change="onAdoptActionChange" class="text-indigo-600" />
                <span>追加相似问法至已有文档</span>
              </label>
            </div>
          </div>

          <div v-if="adoptForm.action === 'ADD_SIMILAR_QUERY'">
            <label class="block font-semibold text-slate-700 mb-1">选择目标知识文档</label>
            <select v-model="adoptForm.target_doc_id" @change="onAdoptTargetDocChange" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="">请选择要追加的文档</option>
              <option v-for="d in documents" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">标准问题 (Standard Question)</label>
            <input v-model="adoptForm.standard_question" type="text" :placeholder="adoptForm.action === 'CREATE_FAQ' ? '系统从簇提取的核心代表问法，可按需微调' : '已从目标知识文档带出标准问法'" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-bold text-slate-900" />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">相似提问表达池 (Similar Queries，每行一个或分号隔开)</label>
            <textarea v-model="adoptForm.similar_questions_text" rows="4" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono leading-relaxed"></textarea>
            <p class="text-[10px] text-slate-400 mt-1">系统已将簇内聚类的用户多形态问法自动填入，可随时增减</p>
          </div>

          <div v-if="adoptForm.action === 'CREATE_FAQ'">
            <label class="block font-semibold text-slate-700 mb-1">标准解答内容 (Answer)</label>
            <textarea v-model="adoptForm.answer" rows="5" placeholder="请录入权威标准的业务解答方案..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 leading-relaxed"></textarea>
          </div>
          <div v-else class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-600 text-xs">
            <span class="font-bold text-slate-700">💡 提示：</span>当前为「追加相似问法至已有文档」模式。提交后系统将直接把上述提问表达池追加至目标文档的相似问中，原文档已有解答内容保持不变。
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
    </div>"""

new_modal_j = """    <!-- 弹窗 J: 采纳 BadCase 簇生成知识草稿 (进入待审核流) -->
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
                <input type="radio" v-model="adoptForm.action" value="CREATE_FAQ" @change="onAdoptActionChange" class="text-indigo-600" />
                <span>新建结构化 FAQ (推荐)</span>
              </label>
              <label class="flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer" :class="adoptForm.action === 'ADD_SIMILAR_QUERY' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold' : 'border-slate-200 text-slate-600'">
                <input type="radio" v-model="adoptForm.action" value="ADD_SIMILAR_QUERY" @change="onAdoptActionChange" class="text-indigo-600" />
                <span>追加相似问法至已有文档</span>
              </label>
            </div>
          </div>

          <!-- 新建结构化 FAQ 模式：必须支持选择目标知识库 -->
          <div v-if="adoptForm.action === 'CREATE_FAQ'">
            <label class="block font-semibold text-slate-700 mb-1">选择归属知识库 (Target Knowledge Base)</label>
            <select v-model="adoptForm.target_kb_id" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option v-for="kb in kbs" :key="kb.id" :value="kb.id">{{ kb.name }} ({{ kb.product_code }})</option>
            </select>
          </div>

          <!-- 追加相似问法模式：选择已有文档 -->
          <div v-if="adoptForm.action === 'ADD_SIMILAR_QUERY'">
            <label class="block font-semibold text-slate-700 mb-1">选择目标知识文档</label>
            <select v-model="adoptForm.target_doc_id" @change="onAdoptTargetDocChange" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="">请选择要追加的文档</option>
              <option v-for="d in documents" :key="d.id" :value="d.id">[{{ d.doc_type }}] {{ d.name }}</option>
            </select>
          </div>

          <!-- 追加相似问法模式：展示目标文档已有解答的只读预览（不让用户填Answer，解答保持不变） -->
          <div v-if="adoptForm.action === 'ADD_SIMILAR_QUERY' && adoptTargetDocInfo" class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
            <div class="text-[11px] font-bold text-slate-700 flex items-center justify-between">
              <span>📖 目标文档已有解答预览（保持原样，无需修改）：</span>
              <span class="text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-medium">仅扩充相似问</span>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">{{ adoptTargetDocInfo.answer || '（该文档暂无独立解答，仅挂载相似问法）' }}</p>
          </div>

          <!-- 新建 FAQ 时输入标准问题 -->
          <div v-if="adoptForm.action === 'CREATE_FAQ'">
            <label class="block font-semibold text-slate-700 mb-1">标准问题 (Standard Question)</label>
            <input v-model="adoptForm.standard_question" type="text" placeholder="系统从簇提取的核心代表问法，可按需微调" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-bold text-slate-900" />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">相似提问表达池 (Similar Queries，每行一个或分号隔开)</label>
            <textarea v-model="adoptForm.similar_questions_text" rows="4" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono leading-relaxed" placeholder="系统已将簇内聚类的用户多形态问法自动填入，可随时增减"></textarea>
            <p class="text-[10px] text-slate-400 mt-1">系统已将簇内聚类的用户多形态问法自动填入，可随时增减</p>
          </div>

          <!-- 仅在新建 FAQ 时展示标准解答录入框；追加相似问模式下彻底隐藏 Answer 输入框！ -->
          <div v-if="adoptForm.action === 'CREATE_FAQ'">
            <label class="block font-semibold text-slate-700 mb-1">标准解答内容 (Answer)</label>
            <textarea v-model="adoptForm.answer" rows="5" placeholder="请录入权威标准的业务解答方案..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 leading-relaxed"></textarea>
          </div>
          <div v-else class="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-start gap-2">
            <span>💡</span>
            <span>当前为<strong>「追加相似问法至已有文档」</strong>模式。提交后系统将直接把上述提问表达池追加至目标文档的相似问中，原文档已有解答内容保持不变。</span>
          </div>

          <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800 flex items-start gap-2">
            <span>ℹ️</span>
            <span><strong>审核流提示：</strong>点击提交后，将在目标知识库 <strong class="text-amber-950 font-mono">《{{ getKbName(adoptForm.target_kb_id || selectedCluster?.kb_id) }}》</strong> 中生成状态为 <span class="font-mono font-bold text-amber-900">PENDING_REVIEW</span> 的知识草稿，由超级管理员审核通过后，才正式构建向量索引生效，防止未经校验的数据污染检索库。</span>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showAdoptModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitAdoptCluster" :disabled="isSubmittingAdopt" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-500/20 cursor-pointer disabled:opacity-50">
            {{ isSubmittingAdopt ? '提交中...' : '确认采纳并提交审核' }}
          </button>
        </div>
      </div>
    </div>"""

assert old_modal_j in html, "old_modal_j not found!"
html = html.replace(old_modal_j, new_modal_j, 1)

# 2. Replace Revise Doc Modal
old_revise_modal = """    <!-- 弹窗: 修订长文本知识库草稿 (场景 C 闭环) -->
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
    </div>"""

new_revise_modal = """    <!-- 弹窗: 修订长文本知识库草稿 (场景 C 闭环) -->
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
            <label class="block font-semibold text-slate-700 mb-1">选择修订目标文档 (Target Document)</label>
            <select v-model="reviseDocForm.doc_id" @change="onReviseDocChange" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">
              <option value="">-- 请选择要修订的文档 --</option>
              <option v-for="d in documents" :key="d.id" :value="d.id">[{{ d.doc_type }}] {{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">修订原因 / 变更说明</label>
            <input v-model="reviseDocForm.change_summary" type="text" placeholder="例如：补充生鲜开封不退例外免责细则" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium" />
          </div>
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block font-semibold text-slate-700">修订后文档完整内容</label>
              <div class="flex items-center gap-2">
                <span v-if="reviseDocForm.current_version" class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">当前版本: v{{ reviseDocForm.current_version }}</span>
                <button 
                  type="button" 
                  @click="resetReviseContentToOriginal"
                  class="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer hover:underline"
                  title="恢复为文档原始未修改内容"
                >
                  ↺ 恢复原文
                </button>
              </div>
            </div>
            <textarea v-model="reviseDocForm.new_content" rows="12" placeholder="在此编辑或增补条款正文..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-mono text-xs focus:ring-1 focus:ring-indigo-500 leading-relaxed"></textarea>
            <div class="flex justify-between items-center text-[10px] text-slate-400 mt-1">
              <span>基于当前文档最新原文编辑增补条款，保存后自动以新版本草稿形式提交超管审核</span>
              <span>{{ (reviseDocForm.new_content || '').length }} 字符</span>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button @click="showReviseDocModal = false" class="px-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-600 cursor-pointer">取消</button>
          <button @click="submitReviseDoc" :disabled="isSubmittingRevise" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md cursor-pointer disabled:opacity-50">
            {{ isSubmittingRevise ? '正在提交草稿...' : '保存并提交审核' }}
          </button>
        </div>
      </div>
    </div>"""

assert old_revise_modal in html, "old_revise_modal not found!"
html = html.replace(old_revise_modal, new_revise_modal, 1)

# 3. Update reactive definitions
old_reactive_adopt = """        const adoptForm = reactive({
          action: 'CREATE_FAQ',
          standard_question: '',
          similar_questions_text: '',
          answer: '',
          target_doc_id: ''
        });"""

new_reactive_adopt = """        const adoptForm = reactive({
          action: 'CREATE_FAQ',
          target_kb_id: '',
          standard_question: '',
          similar_questions_text: '',
          answer: '',
          target_doc_id: ''
        });
        const adoptTargetDocInfo = ref(null);"""

assert old_reactive_adopt in html, "old_reactive_adopt not found!"
html = html.replace(old_reactive_adopt, new_reactive_adopt, 1)

old_reactive_revise = """        const reviseDocForm = reactive({
          doc_id: '',
          doc_name: '',
          current_content: '',
          new_content: '',
          change_summary: '',
          case_id: null,
          cluster_id: null
        });"""

new_reactive_revise = """        const reviseDocForm = reactive({
          doc_id: '',
          doc_name: '',
          current_content: '',
          original_content: '',
          new_content: '',
          current_version: 1,
          change_summary: '',
          case_id: null,
          cluster_id: null
        });"""

assert old_reactive_revise in html, "old_reactive_revise not found!"
html = html.replace(old_reactive_revise, new_reactive_revise, 1)

# 4. Update JS logic for adopt and revise
old_adopt_js = """        const onAdoptActionChange = () => {
          if (adoptForm.action === 'CREATE_FAQ') {
            adoptForm.standard_question = selectedCluster.value?.cluster_name || '';
          } else if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            if (adoptForm.target_doc_id && documents.value) {
              const d = documents.value.find(doc => doc.id === adoptForm.target_doc_id);
              if (d) adoptForm.standard_question = d.name.replace(/\\.(faq|md)$/i, '');
            } else if (selectedCluster.value?.target_knowledge_title) {
              adoptForm.standard_question = selectedCluster.value.target_knowledge_title.replace(/\\.(faq|md)$/i, '');
            }
          }
        };

        const onAdoptTargetDocChange = () => {
          if (adoptForm.action === 'ADD_SIMILAR_QUERY' && adoptForm.target_doc_id && documents.value) {
            const d = documents.value.find(doc => doc.id === adoptForm.target_doc_id);
            if (d) adoptForm.standard_question = d.name.replace(/\\.(faq|md)$/i, '');
          }
        };

        const openAdoptModal = async (c) => {
          selectedCluster.value = c;
          adoptForm.action = c.recommended_action === 'ADD_SIMILAR_QUERY' ? 'ADD_SIMILAR_QUERY' : 'CREATE_FAQ';
          adoptForm.similar_questions_text = (c.sample_queries || []).join('\\n');
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
                adoptForm.standard_question = d.name.replace(/\\.(faq|md)$/i, '');
              } else {
                adoptForm.standard_question = c.target_knowledge_title ? c.target_knowledge_title.replace(/\\.(faq|md)$/i, '') : (c.cluster_name || '');
              }
            } else if (c.target_knowledge_title) {
              adoptForm.standard_question = c.target_knowledge_title.replace(/\\.(faq|md)$/i, '');
            } else {
              adoptForm.standard_question = c.cluster_name || '';
            }
          } else {
            adoptForm.standard_question = c.cluster_name || '';
          }

          showAdoptModal.value = true;
        };

        const submitAdoptCluster = async () => {
          if (adoptForm.action === 'CREATE_FAQ') {
            if (!adoptForm.standard_question.trim()) {
              alert('请输入标准问题');
              return;
            }
            if (!adoptForm.answer.trim()) {
              alert('请输入解答内容');
              return;
            }
          } else if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            if (!adoptForm.target_doc_id) {
              alert('请选择要追加的目标知识文档');
              return;
            }
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
        };"""

new_adopt_js = """        const onAdoptTargetDocChange = async () => {
          if (adoptForm.action === 'ADD_SIMILAR_QUERY' && adoptForm.target_doc_id) {
            if (documents.value) {
              const d = documents.value.find(doc => doc.id === adoptForm.target_doc_id);
              if (d) adoptForm.standard_question = d.name.replace(/\\.(faq|md)$/i, '');
            }
            try {
              const res = await authFetch(`/api/v1/documents/${adoptForm.target_doc_id}`);
              if (res.ok) {
                const docData = await res.json();
                adoptTargetDocInfo.value = {
                  name: docData.doc?.name || '',
                  answer: docData.faq?.answer || (docData.doc?.content || docData.content || '')
                };
              }
            } catch (e) {
              adoptTargetDocInfo.value = null;
            }
          } else {
            adoptTargetDocInfo.value = null;
          }
        };

        const onAdoptActionChange = async () => {
          if (adoptForm.action === 'CREATE_FAQ') {
            adoptForm.standard_question = selectedCluster.value?.cluster_name || '';
            adoptTargetDocInfo.value = null;
          } else if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            await onAdoptTargetDocChange();
          }
        };

        const openAdoptModal = async (c) => {
          selectedCluster.value = c;
          adoptForm.action = c.recommended_action === 'ADD_SIMILAR_QUERY' ? 'ADD_SIMILAR_QUERY' : 'CREATE_FAQ';
          adoptForm.similar_questions_text = (c.sample_queries || []).join('\\n');
          adoptForm.target_doc_id = c.target_knowledge_id || '';
          adoptForm.target_kb_id = c.kb_id || (kbs.value && kbs.value[0]?.id) || '';
          adoptForm.answer = '';
          adoptTargetDocInfo.value = null;

          if (!kbs.value || kbs.value.length === 0) {
            await fetchKBs();
          }
          if (!documents.value || documents.value.length === 0) {
            try {
              const res = await authFetch('/api/v1/documents?page=1&page_size=200');
              if (res.ok) documents.value = await res.json();
            } catch (e) {}
          }

          if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            await onAdoptTargetDocChange();
          } else {
            adoptForm.standard_question = c.cluster_name || '';
          }

          showAdoptModal.value = true;
        };

        const submitAdoptCluster = async () => {
          if (adoptForm.action === 'CREATE_FAQ') {
            if (!adoptForm.target_kb_id) {
              alert('请选择归属目标知识库');
              return;
            }
            if (!adoptForm.standard_question.trim()) {
              alert('请输入标准问题');
              return;
            }
            if (!adoptForm.answer.trim()) {
              alert('请输入解答内容');
              return;
            }
          } else if (adoptForm.action === 'ADD_SIMILAR_QUERY') {
            if (!adoptForm.target_doc_id) {
              alert('请选择要追加的目标知识文档');
              return;
            }
            if (!adoptForm.similar_questions_text.trim()) {
              alert('请输入或保留至少一条相似问法');
              return;
            }
          }
          isSubmittingAdopt.value = true;
          try {
            const rawSim = adoptForm.similar_questions_text.split(/[\\n；;]/).map(s => s.trim()).filter(Boolean);
            const res = await authFetch(`/api/v1/badcases/clusters/${selectedCluster.value.id}/adopt`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                action: adoptForm.action,
                standard_question: adoptForm.standard_question ? adoptForm.standard_question.trim() : "",
                similar_questions: rawSim,
                answer: adoptForm.action === 'CREATE_FAQ' ? adoptForm.answer.trim() : "",
                target_doc_id: adoptForm.target_doc_id || null,
                target_kb_id: adoptForm.target_kb_id || null
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
        };"""

assert old_adopt_js in html, "old_adopt_js not found!"
html = html.replace(old_adopt_js, new_adopt_js, 1)

# 5. Update Revise Doc JS logic
old_revise_js = """        // 修订长文本知识库草稿 (场景 C)
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
        };"""

new_revise_js = """        // 修订长文本知识库草稿 (场景 C)
        const loadDocContentForRevise = async (docId) => {
          if (!docId) return;
          try {
            const res = await authFetch(`/api/v1/documents/${docId}`);
            if (res.ok) {
              const docData = await res.json();
              const fullContent = (docData.doc && docData.doc.content) || docData.content || '';
              reviseDocForm.new_content = fullContent;
              reviseDocForm.original_content = fullContent;
              reviseDocForm.current_version = docData.doc?.version || 1;
              if (docData.doc?.name) {
                reviseDocForm.doc_name = docData.doc.name;
              }
            }
          } catch (e) {
            console.error('加载文档内容失败', e);
          }
        };

        const onReviseDocChange = async () => {
          if (documents.value && reviseDocForm.doc_id) {
            const d = documents.value.find(x => x.id === reviseDocForm.doc_id);
            if (d) reviseDocForm.doc_name = d.name;
          }
          await loadDocContentForRevise(reviseDocForm.doc_id);
        };

        const resetReviseContentToOriginal = () => {
          reviseDocForm.new_content = reviseDocForm.original_content || '';
        };

        const openReviseDocModal = async (docId, docName, caseId = null, clusterId = null) => {
          if (!documents.value || documents.value.length === 0) {
            try {
              const res = await authFetch('/api/v1/documents?page=1&page_size=200');
              if (res.ok) documents.value = await res.json();
            } catch (e) {}
          }
          
          let targetId = docId;
          if (!targetId && documents.value && documents.value.length > 0) {
            targetId = documents.value[0].id;
            docName = documents.value[0].name;
          }

          reviseDocForm.doc_id = targetId || '';
          reviseDocForm.doc_name = docName || '待修订文档';
          reviseDocForm.case_id = caseId;
          reviseDocForm.cluster_id = clusterId;
          reviseDocForm.change_summary = '';
          reviseDocForm.new_content = '正在载入当前文档原文...';
          reviseDocForm.original_content = '';
          reviseDocForm.current_version = 1;
          showReviseDocModal.value = true;

          if (targetId) {
            await loadDocContentForRevise(targetId);
          } else {
            reviseDocForm.new_content = '';
          }
        };"""

assert old_revise_js in html, "old_revise_js not found!"
html = html.replace(old_revise_js, new_revise_js, 1)

# 6. Expose new methods and refs in setup return
old_return = """        openAdoptModal,
        onAdoptActionChange,
        onAdoptTargetDocChange,"""

new_return = """        openAdoptModal,
        onAdoptActionChange,
        onAdoptTargetDocChange,
        adoptTargetDocInfo,
        onReviseDocChange,
        resetReviseContentToOriginal,"""

if old_return in html:
    html = html.replace(old_return, new_return, 1)

with open('app/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Comprehensive patch for index.html completed successfully!")
