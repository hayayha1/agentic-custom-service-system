with open('app/static/index.html', 'r', encoding='utf-8') as f:
    content = f.read().replace('\r\n', '\n')

# 1. Update chat section
old_chat_sec = "<section v-if=\"activeMenu === 'chat'\" class=\"flex-1 flex h-full overflow-hidden\">"
new_chat_sec = "<section v-if=\"activeMenu === 'chat' && hasMenuPermission('chat')\" class=\"flex-1 flex h-full overflow-hidden\">"
assert old_chat_sec in content, "old_chat_sec not found"
content = content.replace(old_chat_sec, new_chat_sec, 1)

# 2. Vue import watch
old_vue_import = "const { createApp, ref, reactive, computed, onMounted, nextTick } = Vue;"
new_vue_import = "const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue;"
assert old_vue_import in content, "old_vue_import not found"
content = content.replace(old_vue_import, new_vue_import, 1)

# 3. hasMenuPermission & watcher
old_has_perm = """        const hasMenuPermission = (menuKey) => {
          if (menuKey === 'chat') return true;
          if (menuKey === 'chunks') return currentRole.value === 'admin' || currentRole.value === 'operator' || currentRole.value === 'tech_agent';
          if (menuKey === 'kb') return currentRole.value === 'admin';
          if (menuKey === 'badcases') return currentRole.value === 'admin' || currentRole.value === 'operator' || currentRole.value === 'tech_agent';
          if (menuKey === 'reports') return currentRole.value === 'admin' || currentRole.value === 'operator' || currentRole.value === 'tech_agent';
          return false;
        };"""

new_has_perm = """        const hasMenuPermission = (menuKey) => {
          if (currentRole.value === 'admin') {
            return true;
          }
          if (currentRole.value === 'operator') {
            // 运营只能看到知识文档管理和badcase池
            return menuKey === 'chunks' || menuKey === 'badcases';
          }
          if (currentRole.value === 'tech_agent') {
            // 客服只能看到对话和知识文档管理
            return menuKey === 'chat' || menuKey === 'chunks';
          }
          if (currentRole.value === 'user') {
            // 普通客户只能看到对话
            return menuKey === 'chat';
          }
          return false;
        };

        // 监听角色与菜单权限，若当前选中的菜单无权访问，自动平滑切至首个有权限菜单
        watch([currentRole, activeMenu], () => {
          if (!hasMenuPermission(activeMenu.value)) {
            if (hasMenuPermission('chat')) {
              activeMenu.value = 'chat';
            } else if (hasMenuPermission('chunks')) {
              activeMenu.value = 'chunks';
            } else if (hasMenuPermission('badcases')) {
              activeMenu.value = 'badcases';
            }
          }
        });"""

assert old_has_perm in content, "old_has_perm not found!"
content = content.replace(old_has_perm, new_has_perm, 1)

# 4. Update badge for reports in menu 5
old_rep_badge = '<span class="text-[9px] bg-rose-500/30 text-rose-200 px-1.5 py-0.2 rounded-full font-mono">全景大盘</span>'
new_rep_badge = '<span class="text-[9px] bg-rose-500/30 text-rose-200 px-1.5 py-0.2 rounded-full font-mono">超管专属</span>'
assert old_rep_badge in content, "old_rep_badge not found!"
content = content.replace(old_rep_badge, new_rep_badge, 1)

with open('app/static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app/static/index.html successfully!")
