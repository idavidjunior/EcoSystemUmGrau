#!/usr/bin/env python3
import sys
sys.path.insert(0, 'scripts')
from widget_grafo import _build_view

result = _build_view()
print('Result:', result)
if result:
    with open(result, 'r', encoding='utf-8') as f:
        content = f.read()
        print('Widget HTML size:', len(content))
        print('Has vendor script tag:', 'vendor/vis-network.min.js' in content)
        print('Has WIDGET_CSS:', 'mk-drag' in content)
        print('Has WIDGET_JS:', 'mk-controles' in content)
        print('Has API_INJECT:', '__widgetApiPoll' in content)
        print('Has groups config:', 'groups:' in content)
        print('Nodes have group:', '"group"' in content)
        # Check for empty catches
        empty_catches = content.count('catch (e) {}') + content.count('catch(e){}')
        print('Empty catches in widget:', empty_catches)
        empty_excepts = content.count('except Exception:') + content.count('except:')
        print('Empty excepts in widget:', empty_excepts)