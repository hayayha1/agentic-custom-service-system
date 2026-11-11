# -*- coding: utf-8 -*-
with open('app/static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update openAdoptModal in index.html
old_open_adopt = """        const openAdoptModal = (c) => {
          selectedCluster.value = c;
          adoptForm.action = c.recommended_action === 'ADD_SIMILAR_QUERY' ? 'ADD_SIMILAR_QUERY' : 'CREATE_FAQ';
          adoptForm.standard_question = c.suggested_standard_query || c.representative_query || '';
          adoptForm.similar_questions_text = (c.sample_queries || []).join('\\n');
          adoptForm.answer = '';
          adoptForm.target_doc_id = '';
          showAdoptModal.value = true;
        };"""

new_open_adopt = """        const onAdoptActionChange = () => {
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
        };"""

if old_open_adopt in content:
    content = content.replace(old_open_adopt, new_open_adopt, 1)
    print('openAdoptModal updated')
else:
    print('old_open_adopt not found')

# 2. Update submitAdoptCluster validation
old_submit_check = """        const submitAdoptCluster = async () => {
          if (!adoptForm.standard_question.trim()) {
            alert('请输入标准问题');
            return;
          }
          if (!adoptForm.answer.trim()) {
            alert('请输入解答内容');
            return;
          }"""

new_submit_check = """        const submitAdoptCluster = async () => {
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
          }"""

if old_submit_check in content:
    content = content.replace(old_submit_check, new_submit_check, 1)
    print('submitAdoptCluster updated')
else:
    print('old_submit_check not found')

# 3. Update return in setup
old_return = 'openAdoptModal,'
new_return = 'openAdoptModal,\n        onAdoptActionChange,\n        onAdoptTargetDocChange,'
if old_return in content:
    content = content.replace(old_return, new_return, 1)
    print('return in setup updated')

# 4. Update Modal Template
old_select = '<select v-model="adoptForm.target_doc_id" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">'
new_select = '<select v-model="adoptForm.target_doc_id" @change="onAdoptTargetDocChange" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium">'
if old_select in content:
    content = content.replace(old_select, new_select, 1)
    print('select change listener added')

old_radio_1 = '<input type="radio" v-model="adoptForm.action" value="CREATE_FAQ" class="text-indigo-600" />'
new_radio_1 = '<input type="radio" v-model="adoptForm.action" value="CREATE_FAQ" @change="onAdoptActionChange" class="text-indigo-600" />'
if old_radio_1 in content:
    content = content.replace(old_radio_1, new_radio_1, 1)

old_radio_2 = '<input type="radio" v-model="adoptForm.action" value="ADD_SIMILAR_QUERY" class="text-indigo-600" />'
new_radio_2 = '<input type="radio" v-model="adoptForm.action" value="ADD_SIMILAR_QUERY" @change="onAdoptActionChange" class="text-indigo-600" />'
if old_radio_2 in content:
    content = content.replace(old_radio_2, new_radio_2, 1)

old_std_q = '<input v-model="adoptForm.standard_question" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-bold text-slate-900" />'
new_std_q = '<input v-model="adoptForm.standard_question" type="text" :placeholder="adoptForm.action === \'CREATE_FAQ\' ? \'系统从簇提取的核心代表问法，可按需微调\' : \'已从目标知识文档带出标准问法\'" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-bold text-slate-900" />'
if old_std_q in content:
    content = content.replace(old_std_q, new_std_q, 1)

old_answer_sec = """          <div>
            <label class="block font-semibold text-slate-700 mb-1">标准解答内容 (Answer)</label>
            <textarea v-model="adoptForm.answer" rows="5" placeholder="请录入权威标准的业务解答方案..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 leading-relaxed"></textarea>
          </div>"""

new_answer_sec = """          <div v-if="adoptForm.action === 'CREATE_FAQ'">
            <label class="block font-semibold text-slate-700 mb-1">标准解答内容 (Answer)</label>
            <textarea v-model="adoptForm.answer" rows="5" placeholder="请录入权威标准的业务解答方案..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 leading-relaxed"></textarea>
          </div>
          <div v-else class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-600 text-xs">
            <span class="font-bold text-slate-700">💡 提示：</span>当前为「追加相似问法至已有文档」模式。提交后系统将直接把上述提问表达池追加至目标文档的相似问中，原文档已有解答内容保持不变。
          </div>"""

if old_answer_sec in content:
    content = content.replace(old_answer_sec, new_answer_sec, 1)
    print('answer section updated')

with open('app/static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('app/static/index.html successfully updated!')
