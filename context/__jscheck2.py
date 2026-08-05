import re
import esprima

src = open('scripts/widget_grafo.py', encoding='utf-8').read()
for name in ['WIDGET_JS_EXTRA', 'WIDGET_JS', 'RESIZE_JS', 'API_INJECT']:
    m = re.search(name + r'\s*=\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', src, re.S)
    if not m:
        print(name, ': NAO ENCONTRADO')
        continue
    val = re.sub(r'%POLL_MS%', '2000', m.group(1))
    js = re.sub(r'</?script>', '', val).strip()
    try:
        esprima.parseScript(js)
        print(name, ': JS OK (%d chars)' % len(js))
    except Exception as e:
        print(name, ': ERRO ->', e)
