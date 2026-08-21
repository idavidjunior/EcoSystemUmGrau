#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')

# Read the widget module
with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\widget_controle_jarvis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the profile_hook import with user_profile import
old_code = """# Perfil do usuário para formatação
try:
    from scripts.profile_hook import format_response_for_profile, get_response_config
    _widget_profile_config = get_response_config()
    WIDGET_PROFILE_AVAILABLE = True
except ImportError as e:
    print(f"[widget] profile_hook não disponível: {e}", flush=True)
    _widget_profile_config = {}
    WIDGET_PROFILE_AVAILABLE = False
    def format_response_for_profile(texto, config):
        return texto
    def get_response_config():
        return {}"""

new_code = """# Perfil do usuário para formatação
try:
    from user_profile import get_profile
    _widget_profile_config = get_profile().get_response_config()
    WIDGET_PROFILE_AVAILABLE = True
except ImportError as e:
    print(f"[widget] user_profile não disponível: {e}", flush=True)
    _widget_profile_config = {}
    WIDGET_PROFILE_AVAILABLE = False
    def format_response_for_profile(texto, config):
        return texto
    def get_response_config():
        return {}"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\widget_controle_jarvis.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Widget import fixed successfully')
else:
    print('Could not find the target code block')
    # Show what's around line 508
    lines = content.split('\n')
    for i in range(505, 525):
        if i < len(lines):
            print(f'{i}: {lines[i][:120]}')