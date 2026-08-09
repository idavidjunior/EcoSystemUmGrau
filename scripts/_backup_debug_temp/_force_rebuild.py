"""Force rebuild and check output."""
import sys
sys.path.insert(0, 'scripts')

# Clear pycache
import os, shutil
for d in ['scripts/__pycache__']:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"Removed {d}")

# Now import fresh
from widget_grafo import WIDGET_JS_EXTRA, RESIZE_JS, _build_view

print("WIDGET_JS_EXTRA len:", len(WIDGET_JS_EXTRA))
print("RESIZE_JS len:", len(RESIZE_JS))

# Check if _build_view works
view = _build_view()
if view:
    content = view.read_text(encoding='utf-8')
    print(f"\nView file: {view}")
    print(f"View size: {len(content)}")
    print(f"mk-btn-3d in output: {content.count('mk-btn-3d')}")
    print(f"painelToggle in output: {content.count('painelToggle')}")
    print(f"btnReset in output: {content.count('btnReset')}")
    print(f"mk-controles in output: {content.count('mk-controles')}")
    print(f"velGroup in output: {content.count('velGroup')}")
    print(f"grupo3D in output: {content.count('grupo3D')}")
else:
    print("BUILD FAILED!")
