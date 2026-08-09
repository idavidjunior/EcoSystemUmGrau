import urllib.request, base64, json

# Verificar sessoes
req = urllib.request.Request('http://127.0.0.1:8767/session')
req.add_header('Authorization', 'Basic ' + base64.b64encode(b'opencode:edbe7432-2bab-454c-b6d5-dd23f9380bba').decode())
resp = urllib.request.urlopen(req, timeout=10)
sessions = json.loads(resp.read().decode())
print(f'Sessoes ativas: {len(sessions)}')

# Criar nova sessao de teste
req2 = urllib.request.Request('http://127.0.0.1:8767/session')
req2.add_header('Authorization', 'Basic ' + base64.b64encode(b'opencode:edbe7432-2bab-454c-b6d5-dd23f9380bba').decode())
req2.add_header('Content-Type', 'application/json')
resp2 = urllib.request.urlopen(req2, data=json.dumps({'title': 'teste'}).encode(), timeout=15)
result = json.loads(resp2.read().decode())
sid = result.get('id')
print(f'Nova sessao: {sid[:20]}...')

# Testar envio de mensagem
if sid:
    req3 = urllib.request.Request(f'http://127.0.0.1:8767/session/{sid}/message')
    req3.add_header('Authorization', 'Basic ' + base64.b64encode(b'opencode:edbe7432-2bab-454c-b6d5-dd23f9380bba').decode())
    req3.add_header('Content-Type', 'application/json')
    body = {'parts': [{'type': 'text', 'text': 'Diga apenas: ok'}]}
    try:
        resp3 = urllib.request.urlopen(req3, data=json.dumps(body).encode(), timeout=30)
        result3 = json.loads(resp3.read().decode())
        print(f'Mensagem enviada com sucesso: {len(result3.get("parts", []))} partes')
    except Exception as e:
        print(f'Erro ao enviar: {e}')
