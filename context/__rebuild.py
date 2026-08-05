import sys
sys.path.insert(0, 'scripts')
import widget_grafo as w

view = w._build_view()
print('view:', view)
if view:
    print('tamanho:', view.stat().st_size)
