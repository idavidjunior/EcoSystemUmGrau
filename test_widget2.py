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
        print('Has widget.css reference:', 'widget.css' in content)
        print('Has widget.js reference:', 'widget.js' in content)
        print('Has widget-extra.js reference:', 'widget-extra.js' in content)
        print('Has api-inject.js reference:', 'api-inject.js' in content)
        print('Has resize.js reference:', 'resize.js' in content)
        print('Has vendor script tag:', 'vendor/vis-network.min.js' in content)
        print('Has groups config:', 'groups:' in content)
        print('Nodes have group:', '"group"' in content)