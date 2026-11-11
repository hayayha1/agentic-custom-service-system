with open('scripts/legacy/patches/build_frontend.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'v-for="(item, idx) in validationReport.items"',
    'v-for="(item, idx) in (validationReport.details || validationReport.items || [])"'
)
c = c.replace(
    ':class="item.score >= 0.75',
    ':class="(item.top_score != null ? item.top_score : item.score) >= 0.70'
)
c = c.replace(
    '{{ (item.score * 100).toFixed(1) }}%',
    '{{ (((item.top_score != null ? item.top_score : item.score) || 0) * 100).toFixed(1) }}%'
)
c = c.replace(
    'item.matched_heading || item.doc_name',
    'item.top_heading || item.top_doc || item.matched_heading'
)

with open('scripts/legacy/patches/build_frontend.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated build_frontend.py modal items')
