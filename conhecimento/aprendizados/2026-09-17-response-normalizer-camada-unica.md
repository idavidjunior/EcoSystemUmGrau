---
tipo: padrao
tags: [response-normalizer, spec, normalizacao, comunicacao, anti-duplicacao]
data: 2026-09-17
contexto: Usuario pediu implementar o ResponseNormalizer da SPEC "Padrão Universal de Resposta do Ecossistema v1.0", verificando duplicacao antes.
decisao: Criar camada única final scripts/response_normalizer.py que reutiliza as peças existentes (validar_idioma, validar_resposta, validar_bajulacao) em vez de duplicar. validar_bajulacao estava órfão no _legado e foi restaurado para scripts/ via git mv, ganhando uso real como dependência do normalizer.
impacto: Nenhuma duplicação criada. Normalizer adiciona etapas que faltavam: tipo de interação, complexidade, estrutura adaptativa, detecção de evidência/incerteza, remoção de redundância, verificação de transparência. Registrado no inventário. Preflights técnico e ético aprovados.
validacao: py_compile OK; caminho feliz, vazio e bajulação testados por --stdin; aderência inventário 85.1% PASS; memória #98360.
licao: Quando a SPEC descreve um componente, verificar antes se peças já cobrem etapas dele (gate pt-BR, detector de bajulação) — o componente orquestra reuso, não reinventa.