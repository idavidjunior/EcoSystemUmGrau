import json
import sys
import importlib.util

spec = importlib.util.spec_from_file_location('m', r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\mcp-composio-server.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m._load_dotenv()

req = {'jsonrpc': '2.0', 'id': 14, 'method': 'tools/call', 'params': {
    'name': 'COMPOSIO_MULTI_EXECUTE_TOOL',
    'arguments': {
        'tools': [
            {'tool_slug': 'GOOGLEDRIVE_FIND_FILE',
             'arguments': {'q': "'root' in parents and trashed = false", 'fields': 'files(id,name,mimeType,size,modifiedTime)', 'pageSize': 500}}
        ],
        'sync_response_to_workbench': True,
        'thought': 'Listar TODOS os arquivos na raiz do Google Drive para planejar a organizacao.',
        'current_step': 'LISTING_ROOT'
    }
}}
r = m.handle(req)
out = json.dumps(r, ensure_ascii=False)
open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_legado\drive_root_raw.json', 'w', encoding='utf-8').write(out)
print('len:', len(out))
print(out[:500])