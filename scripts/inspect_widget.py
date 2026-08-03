import sys
sys.stdout.reconfigure(encoding='utf-8')
d = open('docs/grafo_widget.html', encoding='utf-8').read()
print('network.on presente:', 'network.on' in d)
print("tick string presente:", "'tick'" in d)
print('respiracao presente:', 'respiracao' in d)
print('pulso cognitivo presente:', 'pulso cognitivo' in d)
print('physics enabled true:', 'enabled: true' in d)
print('physics enabled:false NOT frozen:', 'physics: { enabled: false }' not in d)