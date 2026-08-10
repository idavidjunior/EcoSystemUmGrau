---
id: os-automation
categoria: os
nome: os-automation
descricao: "Automação de OS (Windows desktop + Web) para o Jarvis executar ações reais: clicar, digitar, navegar, extrair dados, screenshots. Unifica Playwright (web) e pywinauto (desktop)."
entrypoint: server.py
script: server.py
---

# Skill: os-automation

## Tools

### web_navigate
Navega para URL no browser headless.
- `url` (string, required): URL alvo
- `wait_until` (string, optional): "load" | "domcontentloaded" | "networkidle" (default: "domcontentloaded")
- `timeout_ms` (int, optional): timeout em ms (default: 30000)

### web_click
Clica em elemento via seletor CSS/XPath.
- `selector` (string, required): CSS ou XPath
- `button` (string, optional): "left" | "right" | "middle" (default: "left")
- `count` (int, optional): cliques (default: 1)
- `timeout_ms` (int, optional): timeout (default: 10000)

### web_type
Digita texto em campo.
- `selector` (string, required): CSS ou XPath do input/textarea
- `text` (string, required): texto a digitar
- `delay_ms` (int, optional): delay entre chars (default: 0)
- `clear_first` (bool, optional): limpar antes (default: true)

### web_extract
Extrai dados da página.
- `selector` (string, required): CSS/XPath do elemento ou container
- `attribute` (string, optional): "text" | "html" | "value" | "href" | "src" | atributo custom (default: "text")
- `multiple` (bool, optional): retorna lista se true (default: false)
- `timeout_ms` (int, optional): timeout (default: 10000)

### web_screenshot
Captura screenshot da página ou elemento.
- `path` (string, optional): caminho para salvar (default: temp)
- `selector` (string, optional): elemento específico (default: página inteira)
- `full_page` (bool, optional): página completa (default: true)

### web_wait
Espera condição na página.
- `selector` (string, optional): esperar elemento aparecer
- `state` (string, optional): "attached" | "detached" | "visible" | "hidden" (default: "visible")
- `timeout_ms` (int, optional): timeout (default: 10000)
- `url_contains` (string, optional): esperar URL conter string

### desktop_find_window
Encontra janela por título/classe/regex.
- `title_regex` (string, optional): regex do título
- `class_name` (string, optional): nome da classe da janela
- `process_name` (string, optional): nome do processo (ex: "notepad.exe")

### desktop_click
Clica em coordenadas ou elemento da janela.
- `window_handle` (int, required): handle da janela (do find_window)
- `x` (int, optional): coordenada X relativa à janela
- `y` (int, optional): coordenada Y relativa à janela
- `control_path` (string, optional): caminho do controle UIA (ex: "Button->Edit->List")

### desktop_type
Digita texto em janela/control.
- `window_handle` (int, required): handle da janela
- `text` (string, required): texto
- `control_path` (string, optional): controle específico (default: foco atual)
- `send_keys` (bool, optional): usar SendKeys vs TypeKeys (default: false)

### desktop_screenshot
Captura janela desktop.
- `window_handle` (int, required): handle da janela
- `path` (string, optional): caminho para salvar

### sleep
Pausa execução.
- `seconds` (float, required): segundos

## Dependências
- `playwright` (pip install playwright && playwright install chromium)
- `pywinauto` (pip install pywinauto)
- `uiautomation` (pip install uiautomation) - opcional, para UIA avançado

## Segurança
- Executa em contexto do usuário atual (sem elevação)
- Headless por default no web
- Logs de ações para auditoria