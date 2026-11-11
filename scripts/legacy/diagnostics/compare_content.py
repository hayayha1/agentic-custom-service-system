import sqlite3

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("SELECT content FROM documents WHERE id = 'd3b31441-5fb4-4ea9-80d6-26fd593c6725'")
row = c.fetchone()
db_content = row[0] if row else ""

with open('data/md/01_售后与退换货规则.md', 'r', encoding='utf-8') as f:
    file_content = f.read()

print("DB content len:", len(db_content))
print("File content len:", len(file_content))
print("Match?", db_content.strip() == file_content.strip())
