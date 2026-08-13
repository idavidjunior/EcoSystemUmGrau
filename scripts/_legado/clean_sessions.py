import urllib.request, base64, json

# Listar sessoes
req = urllib.request.Request('http://127.0.0.1:8767/session')
req.add_header('Authorization', 'Basic ' + base64.b64encode(b'opencode:edbe7432-2bab-454c-b6d5-dd23f9380bba').decode())
resp = urllib.request.urlopen(req, timeout=10)
sessions = json.loads(resp.read().decode())
print(f'Total de sessoes: {len(sessions)}')

# Deletar sessoes antigas (manter apenas as 5 ultimas)
if len(sessions) > 5:
    to_delete = sessions[:-5]
    print(f'Deletando {len(to_delete)} sessoes antigas...')
    for s in to_delete:
        sid = s.get('id')
        if sid:
            try:
                req_del = urllib.request.Request(f'http://127.0.0.1:8767/session/{sid}')
                req_del.add_header('Authorization', 'Basic ' + base64.b64encode(b'opencode:edbe7432-2bab-454c-b6d5-dd23f9380bba').decode())
                req_del.get_method = lambda: 'DELETE'
                urllib.request.urlopen(req_del, timeout=5)
            except:
                pass
    print('Limpeza concluida')

# Verificar novamente
resp2 = urllib.request.urlopen(req, timeout=10)
sessions2 = json.loads(resp2.read().decode())
print(f'Sessoes restantes: {len(sessions2)}')
