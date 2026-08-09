import sys,os
BASE=os.path.dirname(os.path.abspath(__file__))
import sys as s; s.path.insert(0,BASE)
import webview
kw={}
kw['resizable']=True
kw['focus']=False
kw['frameless']=True
win=webview.create_window('T', url='http://127.0.0.1:8100/teste_minimo.html', width=500, height=400, x=100, y=100, **kw)
webview.start()
