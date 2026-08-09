#!/usr/bin/env python3
"""Check for duplicate code in widget JS sections."""
with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    content = f.read()

js_sections = [
    ('WIDGET_CSS', 'WIDGET_CSS'),
    ('API_INJECT', 'API_INJECT'),
    ('RESIZE_JS', 'RESIZE_JS'),
    ('WIDGET_JS', 'WIDGET_JS'),
    ('WIDGET_JS_EXTRA', 'WIDGET_JS_EXTRA'),
]

sections = {}
for name, var in js_sections:
    start = content.find(var + ' = """')
    if start != -1:
        start = content.find('"""', start) + 3
        end = content.find('"""', start)
        sections[name] = content[start:end]

# Check for duplicate patterns across sections
for name1, js1 in sections.items():
    for name2, js2 in sections.items():
        if name1 >= name2:
            continue
        lines1 = set([l.strip() for l in js1.split('\n') if len(l.strip()) > 30])
        lines2 = set([l.strip() for l in js2.split('\n') if len(l.strip()) > 30])
        common = lines1 & lines2
        if common:
            print('Duplicate between', name1, 'and', name2)
            for c in list(common)[:5]:
                print('  ', c[:80])

# Check for duplicate CSS rules
css = sections.get('WIDGET_CSS', '')
css_rules = {}
for line in css.split('\n'):
    line = line.strip()
    if '{' in line and '}' not in line:
        selector = line.split('{')[0].strip()
        if selector in css_rules:
            css_rules[selector].append(line)
        else:
            css_rules[selector] = [line]

print('\nDuplicate CSS selectors:')
for selector, rules in css_rules.items():
    if len(rules) > 1:
        print(' ', selector, '->', len(rules), 'times')

# Check for duplicate JS functions/patterns
js_extra = sections.get('WIDGET_JS_EXTRA', '')
# Count mk() function occurrences
mk_count = js_extra.count('function mk(') + js_extra.count('var mk =')
print('\nmk() function definitions:', mk_count)

# Check for duplicate DOM queries
dom_queries = {}
for line in js_extra.split('\n'):
    line = line.strip()
    if 'getElementById' in line or 'querySelector' in line:
        if line in dom_queries:
            dom_queries[line] += 1
        else:
            dom_queries[line] = 1

print('\nRepeated DOM queries:')
for q, count in dom_queries.items():
    if count > 1:
        print(' ', count, 'x:', q[:100])