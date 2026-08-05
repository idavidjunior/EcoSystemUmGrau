import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.widget_grafo as wg

wg._build_view()
print('OK')
