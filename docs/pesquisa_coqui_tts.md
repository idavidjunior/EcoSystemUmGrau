# Pesquisa: Coqui TTS / XTTS-v2 para Ecossistema Jarvis

## Visão Geral

**Coqui TTS** é um toolkit open-source de Text-to-Speech baseado em deep learning.
**XTTS-v2** é o modelo mais avançado, com capacidade de:
- Voice cloning com apenas 3-6 segundos de áudio de referência
- Suporte a 17 idiomas (incluindo Português)
- Fine-tuning para adaptar vozes específicas
- Streaming com latência < 200ms

---

## Suporte a Português (pt-BR)

### Dados de Treinamento
- **2.386,8 horas** de áudio em português no dataset XTTS
- Dados provenientes principalmente do **Common Voice** (Mozilla)
- O modelo já entende pt-BR nativamente

### Vozes Disponíveis
- Vozes multilíngues pré-treinadas
- Capacidade de clonar qualquer voz com amostra de áudio
- Fine-tuning para melhorar qualidade em português específ

---

## Requisitos de Hardware

### Para Inferência (uso normal)
| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| GPU | 8GB VRAM | 12GB+ VRAM |
| RAM | 16GB | 32GB+ |
| CPU | 4 cores | 8+ cores |
| Armazenamento | 10GB | 20GB+ |

### Para Fine-tuning (treinamento)
| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| GPU | 12GB VRAM | 24GB+ VRAM |
| RAM | 32GB | 64GB+ |
| Tempo | 3-8 horas | 1-3 horas |
| Dados | 1-10 horas de áudio | 10-100 horas |

### Notas sobre GPU
- RTX 3060 12GB: Funciona com batch_size=1 (lento)
- RTX 3070/3080 8GB: Usa "CUDA Sysmem Fallback Policy" (usa RAM como extensão)
- RTX 4090 24GB: Ideal para fine-tuning
- A100 40GB+: Profissional, treinamento rápido

---

## Processo de Fine-tuning

### Etapas
1. **Preparação do Dataset**
   - Coletar áudios em português (22050Hz, mono, WAV)
   - Formatar metadata: `audio_path|text|language`
   - Mínimo: 1-10 horas de áudio limpo

2. **Download do Modelo Base**
   ```bash
   # Modelo pré-treinado
   tts --model_name tts_models/multilingual/multi-dataset/xtts_v2
   ```

3. **Configuração do Training**
   - Learning rate: 5e-5 (padrão)
   - Batch size: 1-3 (dependendo da VRAM)
   - Epochs: 50-200
   - Loss weights: Ajustar para priorizar características acústicas

4. **Treinamento**
   ```bash
   # Usando Gradio demo (iniciantes)
   python TTS/demos/xtts_ft_demo/xtts_demo.py
   
   # Avançado
   python recipes/ljspeech/xtts_v2/train_gpt_xtts.py
   ```

5. **Inferência com Modelo Fine-tuned**
   ```python
   from TTS.tts.configs.xtts_config import XttsConfig
   from TTS.tts.models.xtts import Xtts
   
   config = XttsConfig()
   config.load_json("config.json")
   model = Xtts.init_from_config(config)
   model.load_checkpoint(config, checkpoint_path="best_model.pth")
   ```

---

## Opções de Integração

### Opção 1: Servidor Local (Recomendado)
**Prós:**
- Controle total sobre modelo
- Sem dependência de APIs externas
- Possibilidade de fine-tuning contínuo

**Contras:**
- Requer GPU dedicada
- Mais complexo de configurar

**Implementação:**
```bash
# Docker
docker run --gpus all -p 5002:5002 ghcr.io/coqui-ai/tts

# Ou Python direto
tts-server --model_name tts_models/multilingual/multi-dataset/xtts_v2 --use_cuda
```

### Opção 2: API Externa
**Prós:**
- Simples de implementar
- Sem hardware local

**Contras:**
- Custo por uso
- Latência de rede
- Sem fine-tuning

### Opção 3: Híbrido (Recomendado para Ecossistema)
**Prós:**
- Fallback para edge-tts quando GPU indisponível
- Fine-tuning progressivo
- Resiliência

**Implementação:**
```python
# Sistema de fallback
if gpu_disponivel and modelo_fine_tuned:
    usar_coqui_tts(texto)
else:
    usar_edge_tts(texto)  # Atual
```

---

## Comparação com Sistema Atual

| Aspecto | edge-tts (Atual) | Coqui TTS XTTS-v2 |
|---------|------------------|-------------------|
| **Qualidade** | Boa (voz pré-treinada) | Excelente (customizável) |
| **Latência** | ~100ms (rede) | <200ms (local) |
| **Custo** | Gratuito (API Microsoft) | Gratuito (open-source) |
| **Offline** | Não | Sim |
| **Fine-tuning** | Não | Sim |
| **Voice cloning** | Não | Sim (3-6s de áudio) |
| **GPU necessária** | Não | Sim (8GB+ VRAM) |
| **Complexidade** | Baixa | Média-Alta |
| **Controle de entonação** | Limitado | Total |

---

## Estrutura de Diretórios Proposta

```
EcoSystemUmGrau/
├── tts/
│   ├── coqui_tts/
│   │   ├── models/              # Modelos fine-tuned
│   │   ├── voices/              # Amostras de áudio para cloning
│   │   ├── training/            # Scripts de treinamento
│   │   └── config.json          # Configuração do modelo
│   ├── edge_tts/                # Fallback atual
│   └── tts_manager.py           # Gerenciador unificado
├── conhecimento/
│   └── gramatica_pt-br/
│       ├── regras_acentuacao.json
│       ├── concordancia.json
│       ├── crase.json
│       └── fonetica.json
└── scripts/
    ├── tts_server.py            # Servidor Coqui TTS
    ├── fine_tune_tts.py         # Script de fine-tuning
    └── vox_audio.py             # Atualizar para usar novo TTS
```

---

## Plano de Implementação (Futuro)

### Fase 1: Infraestrutura (1-2 dias)
1. Instalar Coqui TTS em ambiente de teste
2. Configurar servidor local
3. Testar inferência básica

### Fase 2: Dataset (2-3 dias)
1. Coletar amostras de áudio em português
2. Formatar para fine-tuning
3. Validar qualidade dos dados

### Fase 3: Fine-tuning (1-2 dias)
1. Treinar modelo com dados portugueses
2. Avaliar qualidade
3. Ajustar hiperparâmetros

### Fase 4: Integração (2-3 dias)
1. Criar gerenciador TTS unificado
2. Atualizar vox_audio.py
3. Testar fallback

### Fase 5: Aprendizado Contínuo (1 semana)
1. Criar sistema de feedback
2. Implementar melhoria contínua
3. Monitorar qualidade

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| GPU insuficiente | Alto | Usar modo CPU ou cloud GPU |
| Qualidade insuficiente | Médio | Ajustar hiperparâmetros, mais dados |
| Complexidade alta | Médio | Começar com fine-tuning simples |
| Incompatibilidade | Baixo | Testar em ambiente isolado primeiro |

---

## Recomendação Final

**Para o Ecossistema Jarvis, recomendo:**

1. **Curto prazo (1-2 semanas):**
   - Manter edge-tts como padrão
   - Instalar Coqui TTS como alternativa
   - Testar com voice cloning simples

2. **Médio prazo (1-2 meses):**
   - Coletar dataset português
   - Fine-tuning do modelo
   - Sistema de fallback automático

3. **Longo prazo (3-6 meses):**
   - Aprendizado contínuo com feedback
   - Múltiplas vozes para diferentes contextos
   - Integração completa com sistema de voz

**Não implementar agora.** Primeiro:
1. Validar que o sistema atual funciona bem
2. Coletar dados de uso (quais textos são falados)
3. Identificar gargalos reais de qualidade

---

## Referências

- [Documentação Coqui TTS](https://docs.coqui.ai/en/stable/)
- [XTTS-v2 no Hugging Face](https://huggingface.co/coqui/XTTS-v2)
- [Fine-tuning Guide](https://docs.coqui.ai/en/stable/finetuning.html)
- [Docker Images](https://docs.coqui.ai/en/latest/docker_images.html)
- [GitHub Repository](https://github.com/coqui-ai/TTS)
