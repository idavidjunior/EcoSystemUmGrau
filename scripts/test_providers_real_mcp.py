#!/usr/bin/env python3
"""Teste dos providers com MCP real."""

import sys
sys.path.insert(0, '.')

from scripts.capability_seams.providers_phase1 import CeticoProvider, EticaProvider, RevisorProvider

# Test all 3 providers with real MCP
for cls in [CeticoProvider, EticaProvider, RevisorProvider]:
    p = cls()
    r = p.execute({'contexto': 'teste'}, {'mission_id': 'test-mcp'})
    print(f'{p.name}: OK - keys={list(r.keys())}')
    if 'fallback' in r:
        print(f'  FALLBACK: {r.get("error_message", "ok")}')
    else:
        print(f'  MCP REAL: {list(r.keys())[:5]}...')