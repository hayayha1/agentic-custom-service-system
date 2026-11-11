with open('app/static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = 'const rawSim = singleAdoptForm.similar_questions_text.split(/['
idx = content.find(target)
print('Found target at:', idx)
if idx != -1:
    end_idx = content.find('map(s => s.trim())', idx)
    print('Target snippet:', repr(content[idx:end_idx]))
    replacement = "const rawSim = (singleAdoptForm.similar_questions_text || '').split(/[;\\n；]/)."
    content = content[:idx] + replacement + content[end_idx:]
    with open('app/static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Successfully updated app/static/index.html')

# Also update scripts/legacy/patches/build_frontend.py
with open('scripts/legacy/patches/build_frontend.py', 'r', encoding='utf-8') as f:
    bf_content = f.read()

bf_idx = bf_content.find(target)
if bf_idx != -1:
    bf_end_idx = bf_content.find('map(s => s.trim())', bf_idx)
    bf_content = bf_content[:bf_idx] + replacement + bf_content[bf_end_idx:]
    with open('scripts/legacy/patches/build_frontend.py', 'w', encoding='utf-8') as f:
        f.write(bf_content)
    print('Successfully updated scripts/legacy/patches/build_frontend.py')
