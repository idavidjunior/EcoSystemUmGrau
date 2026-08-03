import sys
sys.stdout.reconfigure(encoding='utf-8')
d = open('docs/grafo.html', encoding='utf-8').read()
i = d.find("network.on('tick'")
print(d[i-60:i+700])