import os

target = "【场景 A"
for root, dirs, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith(('.py', '.sql', '.json', '.txt', '.md', '.html', '.bak')):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8') as fp:
                    data = fp.read()
                    if target in data:
                        print("Found in:", p)
            except:
                pass
