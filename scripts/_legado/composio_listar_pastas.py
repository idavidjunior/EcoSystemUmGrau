import json
import sys
import importlib.util

spec = importlib.util.spec_from_file_location('m', r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\mcp-composio-server.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m._load_dotenv()

PASTAS = {
    'Codigos AGENTE': '1OV_b5UXvg6Wad1klhknUP0sLUxYl8Rtj',
    'Condominio Apto 155': '1BAHpHSr53BfH2obhPDp8TwqaJFDuPAww',
    'Codigos': '1Hli90SmtOByf0azwQdFb-1MfFNf_OsKA',
    'Livros Historicos': '1l1SJ4fCuBHparJ5QxhJiDVoxyOGNB1BL',
    'GibiMemeHQ': '1t8qGAN6zAKLvbYLMw7X87ValpsWBJH9a',
    'Google AI Studio': '1aJwn_AXN1CVBhzV7fg8nkqTRjrsQb5LV',
    'WEBSIN IA (1)': '115s5J4OQPpfDEkKBhaePtflbFBUYT_SB',
    'TradeUmGrauMOD': '1-pRlBBle5lL22syozF7m8EOcdblAiiam',
    'WEBSIN IA': '1iKDIuqLFzudzxMHUhcke0GFQ29xMXed4',
    'Wallpaper': '10Pt831UX_Xo7bTKuC3HY2G2u3kTMEKQk',
    'Pasta sem titulo': '1hd6K1flOcszSupnkqEKcRmUihrv5V4Vs',
    'Canecas': '1iSUZSdTg4hEPdgUZL8MxqVxpKDgM9dsP',
    'Sapatos Mais Baratos': '1uzer1ScNYd6M5QdiwUsIK9Ck2d439mDo',
    'Sapatos AB': '1oOt54vLV1wGxTtMa_p6cYLciI0uRGZUe',
    'Camisaria': '1Jd7RQJmI5H7gEXUaURk3Fr7bIaGp_0gt',
    'Matriz Bordados': '1uayUXuyxwHo1gjid96b8HQMeYObWzY7v',
    'PLANILHAS EBD': '1UHUnXKp2cxKFRI2E2zW_1gRce7CAfnFH',
    'Praia Juquehy': '1qGOP38O0ZkBXtNGs8s6FJoDm7FsKwVyd',
    'Google Fotos': '1oj7SSVL0DEEasJWYz3txaNqSFOC9EAUb4gw5AomczNo',
    'Temas e Mensagens': '0B9Yibwc8Lytqd19uTHFUY1pKcjQ',
    'Negocio': '0B9Yibwc8LytqYllJcWZCbGRVdEE',
    'DAFE Bordados': '0B9Yibwc8LytqUHZ0aUw0TGNrQ0k',
    'Imagens': '0B9Yibwc8LytqNDM2Mzk2OGMtOTQxNS00NGY1LWE0ZGUtNGUxMGQxYzBmOGFl',
}

tools = []
for nome, fid in PASTAS.items():
    tools.append({'tool_slug': 'GOOGLEDRIVE_FIND_FILE',
                  'arguments': {'q': f"'{fid}' in parents and trashed = false",
                                'fields': 'files(id,name,mimeType)', 'pageSize': 500}})

req = {'jsonrpc': '2.0', 'id': 16, 'method': 'tools/call', 'params': {
    'name': 'COMPOSIO_MULTI_EXECUTE_TOOL',
    'arguments': {'tools': tools, 'sync_response_to_workbench': False,
                  'thought': 'Listar conteudo das pastas originais.', 'current_step': 'LISTING_FOLDERS'}
}}
r = m.handle(req)
txt = r.get('result', {}).get('content', [{}])[0].get('text', '')
open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\_legado\folders_raw.json', 'w', encoding='utf-8').write(txt)
obj = json.loads(txt)
for res in obj.get('data', {}).get('results', []):
    data = res.get('response', {}).get('data', {})
    ok = res.get('response', {}).get('successful')
    files = data.get('files', []) if data else []
    print(f'--- {ok} | {len(files)} itens ---')
    for f in files:
        print('  -', f.get('name'), '|', f.get('mimeType', '').split('.')[-1])