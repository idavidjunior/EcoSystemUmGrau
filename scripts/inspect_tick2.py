import sys
sys.stdout.reconfigure(encoding='utf-8')
d = open('docs/grafo.html', encoding='utf-8').read()
print('tick presente:', "network.on" in d and "'tick'" in d)
print('_tickPausado presente:', '_tickPausado' in d)
print('respiracao presente:', 'respiracao' in d)
print('pulso cognitivo presente:', 'pulso cognitivo' in d)
print('physics enabled true:', "enabled: true" in d or "enabled:true" in d)