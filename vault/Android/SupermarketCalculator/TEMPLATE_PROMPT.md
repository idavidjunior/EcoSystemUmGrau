# Template de Prompt para Criar Qualquer App

## Instruções de uso

1. Copie o template abaixo
2. Substitua o que está entre `[colchetes]` pelas informações do seu app
3. Cole para o desenvolvedor (IA ou humano)
4. Após cada resposta, teste e refine com os templates de iteração no final

---

## Template Principal

---

Quero criar um aplicativo Android chamado **[nome do app]**.

**Objetivo:** [descrição de 1-2 frases do que o app faz]

**Usuário alvo:** [quem vai usar]

**Fluxo principal (passo a passo):**
1. [passo 1]
2. [passo 2]
3. [passo 3]
4. [passo 4]
5. [ passo 5 — continue quantos precisar]

**Dados que o app manipula:** [quais informações o app guarda — ex: itens, preços, datas, nomes...]

**Restrições técnicas (se houver):**
- SDK puro, sem AndroidX, sem Gradle
- Min SDK: [ex: 21]
- Target SDK: [ex: 36]
- Build manual com aapt + javac + d8 + apksigner

**Funcionalidades obrigatórias (MVP):**
- [ ] [funcionalidade essencial 1]
- [ ] [funcionalidade essencial 2]
- [ ] [funcionalidade essencial 3]

**Telas que o app precisa ter:**
1. [tela 1 — o quê aparece]
2. [tela 2 — o quê aparece]
3. [tela 3 — o quê aparece]

**Como quero que os dados sejam salvos:**
- [ex: SharedPreferences para configurações]
- [ex: arquivos em ExternalFilesDir para listas]
- [ex: JSON estruturado para permitir carregar depois]

**Personalização desejada (se houver):**
- [ex: temas de cores]
- [ex: skins diferentes]
- [ex: opções de mostrar/ocultar botões]

**Refinamentos de UX que são importantes:**
- [ex: feedback visual ao clicar]
- [ex: vibração em alertas]
- [ex: destaque no item sendo editado]

---

## Template de Iteração (após testar)

Use este formato cada vez que quiser ajustar ou adicionar algo:

---

**O que eu pedi antes está funcionando, mas quero mais uma alteração:**

[nova funcionalidade ou ajuste]

**Comportamento esperado:**
[o que deveria acontecer quando o usuário faz X]

**Onde deve aparecer:**
[qual tela/região do app]

**Se for um problema (bug):**
O que acontece: [descrição do comportamento atual]
O que deveria acontecer: [descrição do comportamento esperado]

---

## Template de Funcionalidade Avançada

Para pedidos mais complexos, use este formato:

---

**Quero adicionar:**

[descrição clara do que você quer]

**Fluxo detalhado:**
1. [passo 1]
2. [passo 2]
3. [passo 3]

**Dados envolvidos (se houver):**
- [dado 1]
- [dado 2]

**O que já existe no app que pode ser reaproveitado:**
[ex: "já tenho uma lista de itens, só preciso adicionar um botão"]

---

## Exemplo Preenchido (Calculadora de Supermercado)

Para referência, aqui está como o prompt do Supermercado Caixa ficaria preenchido:

---

Quero criar um aplicativo Android chamado **Supermercado Caixa**.

**Objetivo:** Calculadora de compras para supermercado onde o usuário adiciona itens com preço, vê o total acumulado, define orçamento e salva a lista.

**Usuário alvo:** Pessoas fazendo compras no mercado.

**Fluxo principal:**
1. Abre o app
2. Digita o nome do produto (ou escolhe da lista pré-carregada)
3. Digita o preço no teclado numérico
4. Define a quantidade
5. Clica ADICIONAR → item aparece na lista
6. Vê o total atualizado
7. Finaliza a compra → vê recibo → salva ou compartilha

**Dados que o app manipula:** Itens (nome, preço unitário, quantidade), orçamento, listas salvas, configurações de tema e teclado.

**Restrições técnicas:**
- SDK puro, sem AndroidX, sem Gradle
- Min SDK: 21
- Target SDK: 36
- Build manual com aapt + javac + d8 + apksigner

**Funcionalidades obrigatórias:**
- [x] Inserir itens com nome, preço e quantidade
- [x] Teclado numérico customizado (numpad)
- [x] Lista de itens com total por item e total geral
- [x] Orçamento com alertas (80% e 100%)
- [x] Salvar lista em arquivo
- [x] Compartilhar lista
- [x] Três abas: Calculadora, Listas, Config
- [x] Temas (Verde, Escuro, Azul)
- [x] Skin do teclado (Padrão, Arredondado)
- [x] Ocultar botões do teclado (⌫, C, 00, operações)
- [x] Lista pré-carregada de itens da cesta básica
- [x] Itens customizados salvos permanentemente
- [x] Salvar lista como modelo reutilizável
- [x] Comparar listas salvas
- [x] Adicionar todos os itens de uma vez
- [x] Carregar lista salva para editar

**Telas que o app precisa ter:**
1. Calculadora (numpad + input + lista de itens + total + orçamento)
2. Listas (listas salvas, comparar, modelos)
3. Config (tema, personalizar teclado, skin)

**Como quero que os dados sejam salvos:**
- SharedPreferences para tema, configurações do teclado e itens customizados
- Arquivos .txt para recibos legíveis
- Arquivos .json estruturados para carregar/editar/comparar depois

**Personalização desejada:**
- Temas: Verde (padrão), Escuro, Azul
- Skins do teclado: Padrão, Arredondado
- Opções: mostrar/ocultar botões ⌫, C, 00, operações

**Refinamentos de UX importantes:**
- Vibração ao atingir orçamento
- Alerta progressivo (80% → 100%)
- Destaque no item sendo editado
- Edição inline do nome na lista
- Itens da lista pré-carregada aparecem com ✅ quando já adicionados
- "Personalizar..." no fim da lista para adicionar itens que faltam
