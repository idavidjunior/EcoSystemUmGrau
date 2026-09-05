---
id: spec-voxumgrau-exibir-imagem
versao: 0.2.0
status: proposta
componente: Projetos/VoxUmGrau (app Android) + scripts/jarvis_bridge.py (bridge)
tags: [voxumgrau, imagem, websocket, bridge, mapa-mental, base64, compose, graphviz]
data: 2026-09-05
---

# Spec — Exibir Imagem no VoxUmGrau

Permite ao usuário pedir, por voz ou texto, que o Vox mostre um mapa mental,
gráfico, diagrama ou outra representação visual gerada localmente pela bridge,
e permite que o app Android exiba essa imagem dentro da conversa.

## Objetivo

Hoje o app VoxUmGrau processa texto e áudio via WebSocket, mas não possui um
tipo de mensagem visual.

O objetivo desta alteração é permitir solicitações como:

- "mostre um mapa mental sobre redes neurais"
- "faça um diagrama sobre o sistema solar"
- "mostre um gráfico de exemplo"
- "mostre uma figura explicando X"

A bridge deve detectar pedidos de representação visual, gerar uma imagem
localmente sem depender de um serviço pago de geração de imagens e enviá-la
ao app. O app deve exibir a imagem como parte normal do histórico da conversa.

A implementação inicial prioriza diagramas e mapas mentais gerados por
Graphviz ou ferramenta equivalente, em vez de geração artística de imagens.

## Requisitos

### 1. Novo tipo de mensagem

A bridge poderá enviar ao app uma mensagem com:

{
  "tipo": "imagem",
  "base64_png": "<PNG codificado em Base64>",
  "legenda": "Mapa mental sobre redes neurais"
}

Campos:

- `tipo`: valor literal `"imagem"`.
- `base64_png`: conteúdo completo do PNG codificado em Base64.
- `legenda`: texto curto opcional/descritivo para a imagem.

O campo `base64_png` deve ser serializado como string pelo mecanismo JSON
existente. Não deve haver concatenação manual insegura do JSON.

A primeira versão suporta exclusivamente PNG.

### 2. Modelo interno no Android

O Base64 é considerado detalhe de transporte e não deve ser propagado
desnecessariamente pela camada de UI.

Conceitualmente, o app deve representar a mensagem como um novo tipo de
mensagem da conversa:

data class ImageMessage(
    val bytes: ByteArray,
    val legenda: String?
)

A implementação exata pode seguir o modelo de dados já existente no projeto,
desde que a UI não precise conhecer o protocolo WebSocket diretamente.

Fluxo esperado:

WebSocket
    ↓
processarMensagem()
    ↓
decodificação Base64
    ↓
modelo ImageMessage
    ↓
VoxViewModel
    ↓
JarvisChatScreen
    ↓
MessageBubble
    ↓
Image

### 3. Geração da imagem na bridge

A bridge (`scripts/jarvis_bridge.py`) deve:

1. receber a mensagem normal do usuário;
2. detectar se existe intenção de gerar/exibir uma imagem;
3. extrair o assunto/conteúdo solicitado;
4. gerar o diagrama localmente;
5. converter o PNG para Base64;
6. enviar `tipo="imagem"` para o app;
7. continuar o fluxo normal de texto/áudio da conversa.

A geração inicial deve usar uma ferramenta local, preferencialmente
Graphviz, sem depender de uma API paga de geração de imagens.

A arquitetura deve manter a geração desacoplada do WebSocket, conceitualmente:

texto do usuário
      ↓
detecção de intenção
      ↓
DiagramGenerator
      ↓
PNG
      ↓
Base64
      ↓
mensagem WebSocket

A primeira implementação pode possuir somente:

DiagramGenerator
└── GraphvizGenerator

Não é necessário implementar múltiplos geradores nesta versão.

### 4. Detecção de intenção

A detecção inicial deve ser determinística e simples, sem exigir LLM.

Exemplos de gatilhos:

- "mostre um mapa mental"
- "faça um mapa mental"
- "desenhe um diagrama"
- "mostre um diagrama"
- "gere uma figura"
- "mostre uma figura"
- "desenhe um gráfico"

A lista de gatilhos pode ser expandida conforme os testes.

A detecção não precisa ser semanticamente perfeita na v0.2. Caso a bridge não
identifique claramente uma solicitação visual, deve seguir o comportamento
textual existente.

### 5. Exibição no Android

Ao receber:

{
  "tipo": "imagem",
  "base64_png": "...",
  "legenda": "..."
}

o app deve:

1. validar a existência do campo `base64_png`;
2. decodificar o Base64;
3. criar o Bitmap/imagem correspondente;
4. adicionar uma mensagem visual ao histórico;
5. renderizar a imagem através de um `Image` do Jetpack Compose;
6. exibir a legenda quando fornecida.

A nova variante deve ser adicionada ao `MessageBubble` sem alterar o
comportamento dos tipos existentes.

### 6. Imagem como parte da conversa

A imagem deve ser uma mensagem normal do histórico.

Exemplo:

Usuário:
"mostre um mapa mental sobre redes neurais"

Vox:
[imagem do mapa mental]

Vox:
"Esse mapa mostra os principais conceitos..."

A presença da imagem não deve bloquear ou encerrar a conversa.

Depois de uma imagem, o usuário deve poder enviar normalmente outra mensagem
de texto ou solicitar outra imagem.

## Sequenciamento de mensagens

A imagem pode ser enviada junto com o fluxo normal de resposta.

Sequência conceitual:

Usuário
  ↓
mensagem
  ↓
bridge
  ├── imagem
  └── mensagem/áudio

A implementação deve preservar a ordem das mensagens recebidas pelo WebSocket.

A imagem não deve alterar nem interromper:

- `ping/pong`;
- heartbeat;
- grace period;
- `ack`;
- histórico;
- mensagens de texto;
- áudio.

Não é necessário criar um novo tipo de mensagem para erro de geração na v0.2.

## Restrições

- App Android em Kotlin + Jetpack Compose.
- A implementação deve respeitar a arquitetura existente do projeto.
- Não introduzir uma dependência Android desnecessária apenas para renderizar
  PNG.
- A integração deve entrar no pipeline existente:
  `VoxWebSocket -> VoxViewModel -> JarvisChatScreen -> MessageBubble`.
- Bridge em Python.
- Graphviz pode ser usado como dependência externa local.
- A geração da imagem não pode depender de serviço pago de geração de imagens.
- Não quebrar os tipos existentes:
  `mensagem`, `editar`, `ping/pong`, `ack`, `historico`, `audio`.
- Não alterar o comportamento do heartbeat ou do grace period existente.
- O Base64 deve viajar como string dentro de JSON.
- Não realizar concatenação manual de JSON contendo o Base64.

## Limites de tamanho

Para evitar payloads excessivos no WebSocket:

- tamanho alvo do PNG: até aproximadamente 2 MB;
- limite absoluto recomendado: 5 MB;
- imagens acima do limite absoluto não devem ser enviadas como Base64.

Antes da conversão para Base64, a bridge pode redimensionar ou recomprimir a
imagem quando necessário.

Se a imagem ultrapassar o limite:

geração
  ↓
PNG > limite
  ↓
fallback textual

Não enviar apenas um caminho de arquivo local como substituto da imagem, pois
esse caminho não é necessariamente acessível pelo Android.

## Dependências

- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt`
  — recebimento e interpretação dos tipos WebSocket.
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxViewModel.kt`
  — estado e histórico da conversa.
- `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/ui/components/MessageBubble.kt`
  — renderização das mensagens.
- `scripts/jarvis_bridge.py`
  — detecção, geração do PNG e envio da mensagem.
- Ferramenta local de geração de diagramas, preferencialmente Graphviz.

## Premissas

- Existe uma ferramenta de geração de grafos instalada ou instalável no PC.
- Graphviz é suficiente para a primeira versão.
- O fallback textual existente continua funcionando mesmo sem Graphviz.
- O chat atual permite adicionar uma nova variante de mensagem sem refatoração
  estrutural.
- O WebSocket existente aceita mensagens JSON maiores que as mensagens
  textuais normais, respeitando o limite definido nesta spec.

## Entradas e Saídas

### Entrada app → bridge

A entrada continua sendo uma mensagem normal:

{
  "tipo": "mensagem",
  "texto": "mostre um mapa mental sobre redes neurais"
}

### Saída bridge → app

Quando a geração for bem-sucedida:

{
  "tipo": "imagem",
  "base64_png": "<png>",
  "legenda": "Mapa mental sobre redes neurais"
}

A bridge pode posteriormente enviar a resposta textual/áudio normal:

imagem
  ↓
mensagem/áudio

A implementação deve respeitar o mecanismo de sequenciamento já utilizado
pela bridge.

### Efeito no histórico

A imagem passa a fazer parte do histórico da sessão como uma mensagem visual.

O histórico deve continuar funcionando para mensagens textuais e de áudio
existentes.

## Fallback

A geração deve possuir fallback obrigatório.

Casos:

Graphviz disponível + geração OK
    → envia imagem

Graphviz ausente
    → resposta textual

Graphviz falha
    → resposta textual

PNG acima do limite
    → resposta textual

Base64 não pôde ser produzido
    → resposta textual

O fallback deve preservar a funcionalidade atual do Vox.

A resposta textual deve descrever, tanto quanto possível, o conteúdo que seria
representado visualmente.

## Casos de Borda

### Pedido durante setup da bridge

Respeitar o grace period existente.

Não criar tratamento especial que altere o heartbeat.

A imagem deve ser enviada somente quando o socket estiver efetivamente
disponível.

### Imagem muito grande

Aplicar limite antes do envio.

Não enviar payload acima do limite absoluto.

### Geração lenta

A geração não deve bloquear o heartbeat nem impedir o processamento necessário
para manter a conexão viva.

Se a implementação atual da bridge for síncrona, a geração deve ser avaliada
para garantir que não interrompa o mecanismo de ping/pong.

### Geração falhou

Utilizar fallback textual.

### Usuário pede imagem e depois texto

A conversa deve continuar normalmente.

### Usuário pede várias imagens

Cada imagem deve resultar em uma mensagem independente no histórico.

Exemplo:

Usuário → imagem 1 → texto → imagem 2 → texto

### Imagem inválida/corrompida

Se o Android não conseguir decodificar o PNG, não deve derrubar o processamento
das mensagens seguintes.

A mensagem inválida deve ser ignorada ou apresentada como erro visual local,
sem encerrar o WebSocket.

## Compatibilidade

Os tipos existentes devem permanecer inalterados.

O novo comportamento deve ser aditivo:

tipo desconhecido
    → comportamento existente

tipo imagem
    → novo tratamento

demais tipos
    → comportamento atual

Não alterar contratos existentes de:

- `mensagem`;
- `editar`;
- `ping`;
- `pong`;
- `ack`;
- `historico`;
- `audio`.

## Critérios de Aceitação

### WebSocket

- [ ] `VoxWebSocket.kt` reconhece `tipo == "imagem"`.
- [ ] O tratamento de `imagem` não altera o tratamento dos demais tipos.
- [ ] Base64 é decodificado corretamente.
- [ ] PNG inválido não derruba a conexão.
- [ ] Mensagens posteriores continuam sendo processadas.

### Modelo/ViewModel

- [ ] Existe representação interna para mensagem de imagem.
- [ ] A imagem entra no histórico da conversa.
- [ ] A mensagem visual não interrompe o fluxo de texto/áudio.
- [ ] Duas imagens consecutivas podem coexistir no histórico.

### UI

- [ ] `MessageBubble.kt` possui variante visual para imagem.
- [ ] A imagem é renderizada usando Compose `Image`.
- [ ] A legenda é exibida quando presente.
- [ ] A imagem respeita o tamanho disponível da tela.
- [ ] O histórico atual de mensagens continua visualmente funcional.

### Bridge

- [ ] `jarvis_bridge.py` detecta pelo menos os principais gatilhos definidos
  nesta spec.
- [ ] A bridge consegue gerar pelo menos um mapa mental/diagrama usando
  Graphviz.
- [ ] A bridge converte o PNG para Base64.
- [ ] A bridge envia `tipo="imagem"`.
- [ ] O payload respeita o limite máximo definido.
- [ ] Falha de geração produz fallback textual.
- [ ] Ausência do Graphviz produz fallback textual.
- [ ] A geração não impede o heartbeat/grace period.

### Verificação executável

- [ ] O seguinte comando confirma a existência do arquivo principal:

python -c "import os,sys; sys.exit(0 if os.path.exists('Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/VoxWebSocket.kt') else 1)"

### Teste manual

- [ ] Executar o app no aparelho.
- [ ] Pedir: "mostre um mapa mental de X".
- [ ] Verificar a imagem na conversa.
- [ ] Verificar a legenda.
- [ ] Enviar uma nova mensagem depois da imagem.
- [ ] Pedir uma segunda imagem.
- [ ] Verificar que ambas aparecem no histórico.
- [ ] Confirmar que a conexão continua estável.

## Testes Relacionados

### Teste unitário/protocolo

Criar teste para uma mensagem:

{
  "tipo": "imagem",
  "base64_png": "<PNG válido>",
  "legenda": "Teste"
}

Validar:

- parsing;
- decodificação;
- criação da mensagem interna;
- preservação da legenda.

### Teste de fallback

Testar pelo menos:

1. Graphviz indisponível;
2. erro de geração;
3. PNG acima do limite;
4. PNG inválido no Android.

Em todos os casos, o WebSocket deve permanecer funcional.

### Teste de heartbeat

Adaptar ou criar teste baseado em:

`teste_ping_periodico.py`

O teste deve confirmar que a geração/envio de uma imagem não provoca regressão
no heartbeat ou no grace period.

## Definition of Done

- [ ] Bridge gera pelo menos um PNG de diagrama/mapa mental localmente.
- [ ] Bridge envia `tipo=imagem` com Base64.
- [ ] App reconhece `tipo=imagem`.
- [ ] App transforma o payload em mensagem visual.
- [ ] `MessageBubble` renderiza a imagem.
- [ ] Legenda é exibida.
- [ ] Imagem fica persistida no histórico da sessão enquanto o histórico atual
  suportar esse tipo de mensagem.
- [ ] Fallback textual funciona sem Graphviz.
- [ ] Limite de payload está implementado.
- [ ] PNG inválido não derruba a conexão.
- [ ] Teste automatizado/protocolo cobre o novo tipo.
- [ ] Teste de heartbeat/grace period passa.
- [ ] Teste manual no aparelho passa.
- [ ] `installDebug` foi executado com sucesso.
- [ ] Screenshot/evidência do funcionamento foi obtido.
- [ ] Código foi versionado via gate (`persistencia.ps1`).

## Riscos

### Dependência do Graphviz

**Severidade:** média.

Mitigação:

- fallback textual;
- detecção da ausência da ferramenta;
- interface `DiagramGenerator` desacoplada da bridge.

### Payload grande

**Severidade:** média.

Mitigação:

- limite absoluto de tamanho;
- redimensionamento/compressão;
- geração de diagramas com dimensões razoáveis.

### Bloqueio do heartbeat

**Severidade:** alta.

Mitigação:

- geração não deve bloquear o mecanismo de heartbeat;
- testar explicitamente durante geração/envio;
- preservar integralmente o grace period existente.

### Regressão no histórico

**Severidade:** baixa/média.

Mitigação:

- nova variante de mensagem;
- não modificar os tipos existentes;
- testes de mensagens antigas antes e depois da alteração.

### PNG inválido

**Severidade:** baixa.

Mitigação:

- validar/decodificar com segurança;
- não lançar erro que encerre o WebSocket;
- continuar processando mensagens seguintes.

## Arquivos Impactados

Projetos/VoxUmGrau/
├── app/src/main/java/com/voxumgrau/app/
│   ├── VoxWebSocket.kt
│   └── VoxViewModel.kt
│
└── app/src/main/java/com/voxumgrau/app/ui/components/
    └── MessageBubble.kt

scripts/
└── jarvis_bridge.py

testes/
└── teste_ping_periodico.py

A implementação deve evitar alterações fora desses componentes, salvo quando
necessárias para testes, modelos compartilhados ou configuração da dependência
Graphviz.

## Ordem Recomendada de Implementação

1. Definir o modelo interno `ImageMessage`.
2. Implementar parsing de `tipo="imagem"` no `VoxWebSocket`.
3. Integrar `ImageMessage` ao `VoxViewModel`.
4. Adicionar variante de imagem ao `MessageBubble`.
5. Criar `DiagramGenerator` na bridge.
6. Implementar `GraphvizGenerator`.
7. Implementar detecção de intenção.
8. Implementar conversão PNG → Base64.
9. Implementar limite de payload.
10. Implementar fallback textual.
11. Criar testes de protocolo e fallback.
12. Validar heartbeat/grace period.
13. Executar `installDebug`.
14. Testar no aparelho e registrar screenshot/evidência.
15. Executar o gate de persistência/versionamento.

---