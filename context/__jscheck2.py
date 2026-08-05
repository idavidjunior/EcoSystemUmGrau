import re
import esprima

src = open('scripts/widget_grafo.py', encoding='utf-8').read()
# extrai WIDGET_JS_EXTRA e WIDGET_JS e RESIZE_JS e API_INJECT
for name in ['WIDGET_JS_EXTRA', 'WIDGET_JS', 'RESIZE_JS', 'API_INJECT', 'WIDGET_CSS']:
    m = re.search(name + r'\s*=\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', src, re.S)
    if not m:
        print(name, ': NAO ENCONTRADO')
        continue
    val = m.group(1)
    if name.endswith('JS') or name == 'API_INJECT':
        # troca placeholders do tipo %POLL_MS%
        val = re.sub(r'%POLL_MS%', '2000', val)
        # remove <script> tags para validar apenas JS
        js = val
        try:
            esprima.parseScript(js)
            print(name, ': OK (%d chars)' % len(js))
        except Exception as e:
            print(name, ': ERRO ->', e)
    else:
        print(name, ': OK (css %d chars)' % len(val))
