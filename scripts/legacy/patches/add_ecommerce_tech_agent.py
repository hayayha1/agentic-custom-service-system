import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/legacy/patches/build_frontend.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update login card width from max-w-md to max-w-xl
old_container = '<div class="w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl text-white relative z-10 space-y-6">'
new_container = '<div class="w-full max-w-xl bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl text-white relative z-10 space-y-6">'
assert old_container in text, "old_container not found"
text = text.replace(old_container, new_container, 1)

# 2. Update quick fill login buttons
old_quick_login = '''          <div class="grid grid-cols-4 gap-2">
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
          </div>'''

new_quick_login = '''          <div class="grid grid-cols-5 gap-2">
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
          </div>'''

assert old_quick_login in text, "old_quick_login not found"
text = text.replace(old_quick_login, new_quick_login, 1)

# 3. Update roleLabel computed property to distinguish SaaS vs E-commerce customer service
old_role_label = '''        const roleLabels = {
          user: '普通客户',
          tech_agent: '技术客服',
          admin: '超级管理员',
          operator: '知识运营'
        };
        const roleLabel = computed(() => roleLabels[currentRole.value] || '客户');'''

new_role_label = '''        const roleLabels = {
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
        });'''

assert old_role_label in text, "old_role_label not found"
text = text.replace(old_role_label, new_role_label, 1)

# Write back to scripts/legacy/patches/build_frontend.py
with open('scripts/legacy/patches/build_frontend.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("scripts/legacy/patches/build_frontend.py successfully patched with 电商组技术客服!")
