---
tipo: decisao
tags: [traducao, pt-br, audio, texto, localizacao, idioma, clausula-petrea]
data: 2026-08-10
contexto: Usuário pediu para o ecossistema aprender a traduzir textos e áudios para o Português do Brasil (pt-BR) e usar esse aprendizado SEMPRE QUE FOR NECESSÁRIO E SOLICITADO.
decisao: Criar o domínio de conhecimento "Traducao para pt-BR (texto e audio)" no grafo de conhecimento (36 cards em 5 fontes), um hub dedicado no vault, e a CLÁUSULA PÉTREA — TRADUÇÃO PARA O PORTUGUÊS DO BRASIL (TEXTOS E ÁUDIOS) na Constituição para tornar o uso obrigatório e permanente.
impacto: Todo agente do ecossistema traduz textos e áudios para pt-BR com qualidade (fidelidade + naturalidade + formato local) sempre que necessário ou solicitado, seguindo os cards do cluster [[cluster-hub-traducao]].
---

# Mapa do conhecimento de tradução pt-BR

Índice navegável do aprendizado de tradução para o Português do Brasil.
Fonte única dos cards: `ler-runtime/knowledge/knowledge_graph.json` (36 cards novos, patterns 208 → 244).

## Como usar este aprendizado (regra permanente)
- A **CLÁUSULA PÉTREA — TRADUÇÃO PARA O PORTUGUÊS DO BRASIL (TEXTOS E ÁUDIOS)** obriga todo agente a traduzir textos e áudios para pt-BR sempre que necessário ou solicitado.
- Consultar o hub [[cluster-hub-traducao]] antes de traduzir: princípios, estratégias, armadilhas e formatos locais.
- Complemento gramatical: `2026-08-01-gramatica-portugues-br.md`.

## Núcleo de tradução (fonte `traducao`)
- princípios-fundamentais-da-traducao-sentido-equivalência-e-f
- fidelidade-x-naturalidade-quando-priorizar-cada-um
- estratégias-de-tradução-literal-semântica-adaptativa-e-quand
- falsos-cognatos-e-armadilhas-interlíngua-inglês-português
- elementos-culturalmente-intraduzíveis-humor-trocadilhos-prov
- pipeline-de-tradução-de-qualidade-análise-rascunho-revisão-e
- tom-e-registro-formal-técnico-coloquial-como-detectar-e-mant
- quando-adaptar-x-quando-manter-o-termo-original-estrangeiris

## Português do Brasil aplicado (fonte `pt-br`)
- norma-culta-x-coloquial-no-pt-br-quando-usar-cada-registro-n
- variações-pt-pt-x-pt-br-reescrever-para-o-brasileiro
- formas-de-tratamento-em-pt-br-você-tu-senhora-e-concordância
- regionalismos-brasileiros-como-traduzir-sem-cair-em-gírias-m
- siglas-acrônimos-e-nomes-próprios-manter-traduzir-ou-adaptar
- estrangeirismos-no-pt-br-anglicismos-aceitos-aportuguesament

## Tradução por tipo de texto (fonte `traducao-texto`)
- tradução-técnica-manuais-especificações-e-documentação-de-so
- tradução-literária-prosa-e-poesia-ritmo-voz-e-licença-poétic
- tradução-de-interface-e-microcopias-ui-botões-erros-e-textos
- tradução-adaptativa-transcreation-para-marketing-e-publicida
- tradução-jurídica-contratos-e-termos-legais-precisão-e-termi
- tradução-científica-e-acadêmica-papers-abstracts-e-nomenclat
- tradução-jornalística-notícias-manchetes-e-entrevistas
- tradução-de-legendas-embutidas-burned-in-e-placas-de-cena

## Tradução de áudio (fonte `traducao-audio`)
- pipeline-de-tradução-de-áudio-stt-tradução-tts
- dublagem-versão-sincronização-labial-tamanho-da-fala-e-natur
- legendagem-limite-de-caracteres-tempo-em-tela-e-leitura-rápi
- tradução-de-fala-coloquial-e-falas-sobrepostas-em-podcasts-e
- tradução-para-narração-tts-em-pt-br-pontuação-entonação-e-ss
- sotaques-e-variantes-do-português-falado-transcrever-sem-dis
- tradução-de-músicas-e-letras-adaptação-rítmica-x-tradução-li
- timing-e-sincronização-de-legendas-duração-mínima-cps-e-cort
- palavras-de-preenchimento-hesitações-e-ruído-na-transcrição-

## Localização (fonte `localizacao`)
- localização-l10n-vs-internacionalização-i18n-vs-transcreatio
- datas-horas-e-fuso-horário-no-brasil-ddmmaaaa-24h-brt
- números-moedas-r-e-percentuais-no-pt-br
- unidades-de-medida-e-convenções-brasileiras-m-kg-c-telefone-
- localização-de-software-placeholders-plurais-gênero-e-espaço

## Consistência
- Grafo: 244 patterns (36 novos de tradução), fonte única `ler-runtime/knowledge/knowledge_graph.json`.
- Vault: `cluster-hub-traducao.md` com as 36 notas; `home.md` lista o cluster.
- Regras: cláusula pétrea de tradução adicionada à Constituição (3 camadas sincronizadas).
- Atenção: o runtime LER pode reconsolidar o grafo a partir de processos antigos; se o count voltar abaixo de 244, re-executar o ingest dos cards (`ingest_traducao.py` na pasta temp).

## Conexoes

- [[cluster-hub-traducao]]
- [[elementos-culturalmente-intraduzíveis-humor-trocadilhos-prov]]
- [[estratégias-de-tradução-literal-semântica-adaptativa-e-quand]]
- [[falsos-cognatos-e-armadilhas-interlíngua-inglês-português]]
- [[fidelidade-x-naturalidade-quando-priorizar-cada-um]]
- [[localização-l10n-vs-internacionalização-i18n-vs-transcreatio]]
- [[norma-culta-x-coloquial-no-pt-br-quando-usar-cada-registro-n]]
- [[pipeline-de-tradução-de-qualidade-análise-rascunho-revisão-e]]
- [[princípios-fundamentais-da-tradução-sentido-equivalência-e-f]]
- [[quando-adaptar-x-quando-manter-o-termo-original-estrangeiris]]
- [[tom-e-registro-formal-técnico-coloquial-como-detectar-e-mant]]