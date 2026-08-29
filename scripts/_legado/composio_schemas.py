import json
import sys
import importlib.util

spec = importlib.util.spec_from_file_location('m', r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\mcp-composio-server.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m._load_dotenv()

req = {'jsonrpc': '2.0', 'id': 9, 'method': 'tools/call', 'params': {
    'name': 'COMPOSIO_GET_TOOL_SCHEMAS',
    'arguments': {'tool_slugs': ['GOOGLEDRIVE_FIND_FILE', 'GOOGLEDRIVE_CREATE_FOLDER', 'GOOGLEDRIVE_MOVE_FILE', 'GOOGLEDRIVE_DELETE_FILE', 'GOOGLEDRIVE_GET_ABOUT']}
}}
r = m.handle(req)
txt = r.get('result', {}).get('content', [{}])[0].get('text', '')
d = json.loads(txt)
for slug, sch in d.get('data', {}).get('tool_schemas', {}).items():
    props = sch.get('input_schema', {}).get('properties', {})
    reqs = sch.get('input_schema', {}).get('required', [])
    print('=== ' + slug + ' ===')
    print('required:', reqs)
    for k, v in props.items():
        desc = str(v.get('description'))[:90]
        print('  ' + k + ': ' + str(v.get('type')) + ' - ' + desc)
    print()