#!/usr/bin/env python3
"""Teste da interface do conversor de bordado."""

import sys
sys.path.append('Projetos/ConversorBordado')

# Mock de tkinter para testar sem display
class MockTk:
    def __init__(self):
        self.tk = self
        self._title = ""
        self._geometry = ""
        
    def title(self, t):
        self._title = t
        
    def geometry(self, g):
        self._geometry = g
        
    def columnconfigure(self, c, **kwargs):
        pass
        
    def rowconfigure(self, r, **kwargs):
        pass
        
    def mainloop(self):
        pass
        
    def update(self):
        pass

# Mock de ttk
class MockTtk:
    class Frame:
        def __init__(self, parent, **kwargs):
            pass
        def grid(self, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
        def columnconfigure(self, c, **kwargs):
            pass
        def rowconfigure(self, r, **kwargs):
            pass
            
    class Label:
        def __init__(self, parent, **kwargs):
            pass
        def grid(self, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
        def config(self, **kwargs):
            pass
            
    class Button:
        def __init__(self, parent, **kwargs):
            pass
        def grid(self, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
            
    class LabelFrame:
        def __init__(self, parent, **kwargs):
            pass
        def grid(self, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
            
    class Radiobutton:
        def __init__(self, parent, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
            
    class Combobox:
        def __init__(self, parent, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
            
    class Scale:
        def __init__(self, parent, **kwargs):
            pass
        def pack(self, **kwargs):
            pass
            
    class Spinbox:
        def __init__(self, parent, **kwargs):
            pass
        def pack(self, **kwargs):
            pass

# Substituir módulos reais pelos mocks
import tkinter
import tkinter.ttk
sys.modules['tkinter'] = MockTk()
sys.modules['tkinter.ttk'] = MockTtk()
sys.modules['tkinter.filedialog'] = type(sys)('filedialog')
sys.modules['tkinter.messagebox'] = type(sys)('messagebox')
sys.modules['tkinter ImageTk'] = type(sys)('ImageTk')

# Agora importar o conversor
from conversor import ConversorBordado

def test_interface():
    """Testa a interface do conversor."""
    # Criar instância com mock
    root = MockTk()
    conversor = ConversorBordado(root)
    
    # Verificar se a interface foi criada
    assert conversor.root == root
    assert conversor.image_path is None
    assert conversor.mode_var.get() == "auto"
    assert conversor.format_var.get() == "DST"
    
    print("✓ Interface criada com sucesso")
    print(f"  Título: {root._title}")
    print(f"  Geometria: {root._geometry}")
    
    # Verificar métodos
    assert hasattr(conversor, 'upload_image')
    assert hasattr(conversor, 'convert_image')
    assert hasattr(conversor, 'auto_convert')
    assert hasattr(conversor, 'manual_convert')
    
    print("✓ Todos os métodos existem")
    
    return True

if __name__ == "__main__":
    print("Teste da interface do conversor:")
    test_interface()
    print("\n✓ Teste da interface concluído!")