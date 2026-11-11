import re

with open("app/static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. 提取错误位置的 Tab 2 和 Tab 3 HTML
# 错误位置位于活跃菜单为 chat 的尾部
wrong_start_marker = "          </div> <!-- 关闭 Tab 1 -->"
wrong_end_marker = "        <!-- ================= 模块 2: 知识片段与文档治理 ================= -->"

start_pos = html.find(wrong_start_marker)
end_pos = html.find(wrong_end_marker)

if start_pos != -1 and end_pos != -1:
    print(f"Found misplaced tabs between {start_pos} and {end_pos}")
    # 提取 Tab 2 和 Tab 3 内容（从 Tab 2 开始到 Tab 3 结束，不包含末尾的 </section>）
    tab2_start = html.find("<!-- ================= Tab 2: 全量 BadCase 池与长尾治理 ================= -->", start_pos)
    # Tab 3 结束在倒数第一个 </section> 前面
    section_close_pos = html.rfind("</section>", start_pos, end_pos)
    
    tabs_content = html[tab2_start:section_close_pos].strip()
    
    # 恢复 Chat 区域的正常闭合
    clean_chat_end = """          </div>
        </section>

"""
    html = html[:start_pos] + clean_chat_end + html[end_pos:]
    print("Cleaned chat section successfully.")

    # 2. 将 Tab 2 和 Tab 3 放到正确的 BadCase 区域尾部
    # BadCase 区域的结尾在模块 4 的 </section>
    badcase_section_marker = "        <section v-if=\"activeMenu === 'badcases' && hasMenuPermission('badcases')\""
    badcase_pos = html.find(badcase_section_marker)
    if badcase_pos != -1:
        badcase_end_marker = "</section>\n\n      </main>"
        b_end_pos = html.find(badcase_end_marker, badcase_pos)
        if b_end_pos == -1:
            badcase_end_marker = "</section>"
            b_end_pos = html.find(badcase_end_marker, badcase_pos)
        
        # 在 </section> 前闭合 Tab 1，并插入 Tab 2 和 Tab 3
        correct_insertion = f"""          </div> <!-- 关闭 Tab 1 -->

          {tabs_content}
        """
        html = html[:b_end_pos] + correct_insertion + html[b_end_pos:]
        print("Inserted tabs into BadCase section successfully.")

# 3. 检查并确保 singleAdoptForm.similar_questions_text 正则格式干净
target_regex = "const rawSim = singleAdoptForm.similar_questions_text.split(/["
if target_regex in html:
    idx = html.find(target_regex)
    end_idx = html.find("map(s => s.trim())", idx)
    html = html[:idx] + "const rawSim = (singleAdoptForm.similar_questions_text || '').split(/[;\\n；]/)." + html[end_idx:]

with open("app/static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

with open("scripts/legacy/patches/build_frontend.py", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved cleanly to app/static/index.html and scripts/legacy/patches/build_frontend.py")
