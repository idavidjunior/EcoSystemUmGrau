"""validar_idioma.py — Valida se um texto está em Português do Brasil (pt-BR).

Uso:
  python scripts/validar_idioma.py "texto a validar"
  echo "texto" | python scripts/validar_idioma.py --stdin

Exit: 0 = pt-BR, 1 = não-pt-BR, 2 = erro
"""
import re
import sys

# Palavras comuns em português (artigos, preposições, conjunções, pronomes, verbos, técnicos)
PALAVRAS_PT = {
    # Artigos
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    # Preposições
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "sob", "entre", "até", "desde",
    "após", "antes", "durante", "contra", "perante", "trás",
    "num", "nuns", "numa", "numas",  # contrações
    # Conjunções
    "e", "ou", "mas", "porém", "contudo", "todavia", "entretanto",
    "que", "se", "pois", "porque", "como", "quando", "onde",
    "logo", "assim", "então", "portanto", "pois", "porquanto",
    # Pronomes
    "eu", "tu", "ele", "ela", "nós", "vocês", "eles", "elas",
    "me", "te", "se", "nos", "vos", "meu", "teu", "seu", "sua",
    "nosso", "nosso", "você", "você", "mim", "ti", "si",
    # Verbos comuns (infinitivo e conjugados)
    "é", "está", "são", "tem", "pode", "deve", "fazer", "dizer",
    "ir", "vir", "dar", "ver", "saber", "querer", "poder",
    "ter", "ser", "estar", "haver", "ficar", "trazer", "levar",
    "foi", "era", "vai", "vem", "dá", "vê", "sabe", "quer",
    "fez", "disse", "veio", "deu", "vi", "sei", "quis",
    "estava", "estavam", "tinha", "tinham", "podia", "podiam",
    "devia", "devam", "faça", "façam", "diga", "digam",
    "exibe", "exibem", "exibiu", "exibir",
    "mostra", "mostram", "mostrou", "mostrar",
    "identificar", "identifica", "identificou", "identifique",
    "verificar", "verifica", "verificou", "verifique",
    "investigar", "investiga", "investigou", "investigue",
    "aparece", "aparecem", "apareceu", "aparecer",
    "funciona", "funcionam", "funcionou", "funcionar",
    "rodando", "roda", "rode",
    "parar", "para", "parou", "pare",
    "reiniciar", "reinicia", "reiniciou", "reiniciar",
    "conectar", "conecta", "conectou", "conectar",
    # Termos técnicos comuns em pt-BR
    "widget", "toast", "erro", "erros", "falha", "falhas",
    "log", "logs", "debug", "debugar",
    "conexão", "conexao", "rede", "servidor", "cliente",
    "banco", "dados", "tabela", "query", "sql",
    "arquivo", "arquivos", "pasta", "pastas",
    "config", "configuração", "configuracao", "configurar",
    "script", "scripts", "código", "codigo", "programa",
    "tela", "janela", "botão", "botao", "clique", "clicar",
    "mouse", "teclado", "tecla", "enter", "escape",
    "audio", "som", "voz", "fala", "falar", "fala",
    "microfone", "microphone", "speaker", "speaker",
    "volume", "mudo", "mutado", "unmute",
    "notificação", "notificacao", "alert", "alerta",
    "janela", "abas", "tab", "abas",
    "menu", "menus", "opção", "opcao", "opções", "opcoes",
    "item", "itens", "lista", "listas", "item",
    "salvar", "salva", "salvou", "save",
    "carregar", "carrega", "carregou", "load",
    "abrir", "abre", "abriu", "open",
    "fechar", "fecha", "fechou", "close",
    "minimizar", "minimiza", "minimizou",
    "maximizar", "maximiza", "maximizou",
    "restaurar", "restaura", "restaurou",
    # Adjetivos/advérbios comuns
    "bom", "mau", "grande", "pequeno", "novo", "velho",
    "muito", "pouco", "mais", "menos", "também", "já",
    "agora", "hoje", "amanhã", "ontem", "sempre", "nunca",
    "aqui", "ali", "lá", "cá", "longe", "perto",
    "bem", "mal", "melhor", "pior", "certo", "errado",
    "pronto", "prontos", "feito", "feitos",
    "mesmo", "mesma", "mesmos", "mesmas",
    "outro", "outra", "outros", "outras",
    "tal", "tais", "talvez", "provavelmente",
    # Números/quantificadores
    "um", "dois", "três", "quatro", "cinco", "muita", "muitos",
    "poucos", "pouca", "todos", "todas", "cada", "qualquer",
    "vários", "varias", "alguns", "algumas",
    # Expressões
    "não", "sim", "obrigado", "por favor", "desculpe",
    "obrigada", "valeu", "legal", "certo", "exato",
    "claro", "clara", "óbvio", "obvio", "natural",
    "entendi", "entendido", "compreendi", "entender",
    # Preposições extras
    "por", "para", "com", "sem", "sob", "entre", "até", "desde",
    "após", "antes", "durante", "contra", "perante", "trás",
    "num", "nuns", "numa", "numas",
    # Conjunções extras
    "e", "ou", "mas", "porém", "contudo", "todavia", "entretanto",
    "que", "se", "pois", "porque", "como", "quando", "onde",
    "logo", "assim", "então", "portanto", "pois", "porquanto",
    # Pronomes extras
    "eu", "tu", "ele", "ela", "nós", "vocês", "eles", "elas",
    "me", "te", "se", "nos", "vos", "meu", "teu", "seu", "sua",
    "nosso", "nosso", "você", "você", "mim", "ti", "si",
    # Verbos extras
    "é", "está", "são", "tem", "pode", "deve", "fazer", "dizer",
    "ir", "vir", "dar", "ver", "saber", "querer", "poder",
    "ter", "ser", "estar", "haver", "ficar", "trazer", "levar",
    "foi", "era", "vai", "vem", "dá", "vê", "sabe", "quer",
    "fez", "disse", "veio", "deu", "vi", "sei", "quis",
    "estava", "estavam", "tinha", "tinham", "podia", "podiam",
    "devia", "devam", "faça", "façam", "diga", "digam",
    # Adjetivos/advérbios comuns
    "bom", "mau", "grande", "pequeno", "novo", "velho",
    "muito", "pouco", "mais", "menos", "também", "já",
    "agora", "hoje", "amanhã", "ontem", "sempre", "nunca",
    "aqui", "ali", "lá", "cá", "longe", "perto",
    "bem", "mal", "melhor", "pior", "certo", "errado",
    "pronto", "prontos", "feito", "feitos",
    "mesmo", "mesma", "mesmos", "mesmas",
    "outro", "outra", "outros", "outras",
    "tal", "tais", "talvez", "provavelmente",
    # Números/quantificadores
    "um", "dois", "três", "quatro", "cinco", "muita", "muitos",
    "poucos", "pouca", "todos", "todas", "cada", "qualquer",
    "vários", "varias", "alguns", "algumas",
    # Expressões
    "não", "sim", "obrigado", "por favor", "desculpe",
    "obrigada", "valeu", "legal", "certo", "exato",
    "claro", "clara", "óbvio", "obvio", "natural",
    "entendi", "entendido", "compreendi", "entender",
    # Termos técnicos
    "widget", "toast", "erro", "erros", "falha", "falhas",
    "log", "logs", "debug", "debugar",
    "conexão", "conexao", "rede", "servidor", "cliente",
    "banco", "dados", "tabela", "query", "sql",
    "arquivo", "arquivos", "pasta", "pastas",
    "config", "configuração", "configuracao", "configurar",
    "script", "scripts", "código", "codigo", "programa",
    "tela", "janela", "botão", "botao", "clique", "clicar",
    "mouse", "teclado", "tecla", "enter", "escape",
    "audio", "som", "voz", "fala", "falar", "fala",
    "microfone", "microphone", "speaker", "speaker",
    "volume", "mudo", "mutado", "unmute",
    "notificação", "notificacao", "alert", "alerta",
    "janela", "abas", "tab", "abas",
    "menu", "menus", "opção", "opcao", "opções", "opcoes",
    "item", "itens", "lista", "listas", "item",
    "salvar", "salva", "salvou", "save",
    "carregar", "carrega", "carregou", "load",
    "abrir", "abre", "abriu", "open",
    "fechar", "fecha", "fechou", "close",
    "minimizar", "minimiza", "minimizou",
    "maximizar", "maximiza", "maximizou",
    "restaurar", "restaura", "restaurou",
    "exibe", "exibem", "exibiu", "exibir",
    "mostra", "mostram", "mostrou", "mostrar",
    "identificar", "identifica", "identificou", "identifique",
    "verificar", "verifica", "verificou", "verifique",
    "investigar", "investiga", "investigou", "investigue",
    "aparece", "aparecem", "apareceu", "aparecer",
    "funciona", "funcionam", "funcionou", "funcionar",
    "rodando", "roda", "rode",
    "parar", "para", "parou", "pare",
    "reiniciar", "reinicia", "reiniciou", "reiniciar",
    "conectar", "conecta", "conectou", "conectar",
    # Adjetivos/advérbios comuns
    "bom", "mau", "grande", "pequeno", "novo", "velho",
    "muito", "pouco", "mais", "menos", "também", "já",
    "agora", "hoje", "amanhã", "ontem", "sempre", "nunca",
    "aqui", "ali", "lá", "cá", "longe", "perto",
    "bem", "mal", "melhor", "pior", "certo", "errado",
    "pronto", "prontos", "feito", "feitos",
    "mesmo", "mesma", "mesmos", "mesmas",
    "outro", "outra", "outros", "outras",
    "tal", "tais", "talvez", "provavelmente",
    # Números/quantificadores
    "um", "dois", "três", "quatro", "cinco", "muita", "muitos",
    "poucos", "pouca", "todos", "todas", "cada", "qualquer",
    "vários", "varias", "alguns", "algumas",
    # Expressões
    "não", "sim", "obrigado", "por favor", "desculpe",
    "obrigada", "valeu", "legal", "certo", "exato",
    "claro", "clara", "óbvio", "obvio", "natural",
    "entendi", "entendido", "compreendi", "entender",
    # Preposições
    "num", "nuns", "numa", "numas",
    # Contrações
    "pelo", "pela", "pelos", "pelas",
    "pelo", "pela", "pelos", "pelas",
    # Verbos de ação
    "rodar", "roda", "rodou", "rodar",
    "executar", "executa", "executou",
    "processar", "processa", "processou",
    "analisar", "analisa", "analisou",
    "monitorar", "monitora", "monitorou",
    "detectar", "detecta", "detectou",
    "corrigir", "corrige", "corrigiu",
    "resolver", "resolve", "resolveu",
    "testar", "testa", "testou",
    "validar", "valida", "validou",
    "compilar", "compila", "compilou",
    "instalar", "instala", "instalou",
    "atualizar", "atualiza", "atualizou",
}

# Caracteres específicos do português (acentos, cedilha, til)
CARACTERES_PT = set("ãõáàâéêíóôúçÃÕÁÀÂÉÊÍÓÔÚÇ")

# Padrões de palavras pt-BR (terminações comuns)
SUFIXOS_PT = ["ção", "ções", "mente", "oso", "osa", "ável", "ível", "inho", "inha"]


def calcular_score_pt(texto: str) -> float:
    """Calcula um score de 0 a 100 indicando probabilidade de ser pt-BR."""
    if not texto or not texto.strip():
        return 0.0

    texto_lower = texto.lower()
    # Filtrar apenas palavras alfanuméricas (ignora números puros, URLs, códigos)
    palavras = [p for p in re.findall(r'\b\w+\b', texto_lower) 
                if not p.isdigit() and len(p) > 1]

    if not palavras:
        return 0.0

    # 1. Score por palavras conhecidas (peso: 50%)
    palavras_pt = sum(1 for p in palavras if p in PALAVRAS_PT)
    score_palavras = (palavras_pt / len(palavras)) * 100

    # 2. Score por caracteres pt-BR (peso: 20%)
    chars_total = len(texto)
    chars_pt = sum(1 for c in texto if c in CARACTERES_PT)
    score_chars = (chars_pt / max(chars_total, 1)) * 100

    # 3. Score por sufixos pt-BR (peso: 15%)
    sufixos = sum(1 for p in palavras if any(p.endswith(s) for s in SUFIXOS_PT))
    score_sufixos = (sufixos / len(palavras)) * 100

    # 4. Bonus para textos curtos que têm pelo menos 1 palavra pt-BR
    palavras_pt_count = sum(1 for p in palavras if p in PALAVRAS_PT)
    bonus_curto = 0
    if len(palavras) <= 5 and palavras_pt_count > 0:
        bonus_curto = 15  # ajuda textos curtos legítimos

    # Peso final ajustado
    score_final = (score_palavras * 0.5) + (min(score_chars, 100) * 0.2) + (score_sufixos * 0.15) + bonus_curto

    return min(score_final, 100.0)


def validar_idioma(texto: str, threshold: float = 30.0) -> dict:
    """Valida se o texto está em pt-BR.

    Args:
        texto: Texto a validar
        threshold: Score mínimo para considerar pt-BR (padrão: 30)

    Returns:
        dict com 'ok' (bool), 'score' (float), 'idioma' (str)
    """
    score = calcular_score_pt(texto)
    ok = score >= threshold

    return {
        "ok": ok,
        "score": round(score, 2),
        "idioma": "pt-BR" if ok else "desconhecido",
        "threshold": threshold,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        texto = sys.stdin.read()
    elif len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
    else:
        print("Uso: python validar_idioma.py \"texto\" ou echo \"texto\" | python validar_idioma.py --stdin")
        sys.exit(2)

    resultado = validar_idioma(texto)

    if resultado["ok"]:
        print(f"[OK] pt-BR detectado (score: {resultado['score']})")
        sys.exit(0)
    else:
        print(f"[FALHA] Não-pt-BR detectado (score: {resultado['score']}, threshold: {resultado['threshold']})")
        sys.exit(1)


if __name__ == "__main__":
    main()