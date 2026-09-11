# Conversor de Imagem para Bordado

Interface desktop em Python para converter imagens em arquivos de bordado.

## Funcionalidades
- Upload de imagem (JPG, PNG, GIF, BMP)
- Conversão automática e manual
- 3 níveis de qualidade: Normal, Média, Super Alta
- 4 níveis de precisão: Baixa, Normal, Alta, Muito Alta
- Reforço do bordado para relevo grosso:
  - Satin Denso
  - Fill Triplo
  - Cadeia Grossa
- Prévia do bordado antes de salvar:
  - Prévia realista (simulação de tecido)
  - Prévia wireframe (caminhos dos pontos)
- Exportação nos formatos: DST, PES, JEF, EXP, XXX

## Tecnologias
- Python 3
- tkinter (interface desktop)
- pyembroidery (motor de conversão)
- Pillow (processamento de imagem)

## Instalação
1. Instalar Python 3.8+
2. Instalar dependências:
   ```bash
   pip install pyembroidery pillow
   ```

## Uso
1. Executar o conversor:
   ```bash
   python conversor.py
   ```
2. Clicar em "Selecionar Imagem" para carregar uma imagem
3. Escolher o modo (Automático ou Manual)
4. Configurar qualidade e precisão
5. Ativar reforço se desejar bordado mais cheio e com relevo
6. Clicar em "Gerar Prévia" para ver como ficará o bordado
7. Clicar em "Converter e Salvar" para exportar o arquivo

## Configurações de Qualidade

### Normal
- Densidade: 0.3
- Passo: 4 pixels
- Espessura: 1
- Ideal para: bordados simples e rápidos

### Média
- Densidade: 0.5
- Passo: 3 pixels
- Espessura: 2
- Ideal para: bordados com bom equilíbrio entre qualidade e velocidade

### Super Alta
- Densidade: 0.8
- Passo: 2 pixels
- Espessura: 3
- Ideal para: bordados de alta qualidade com muitos detalhes

## Configurações de Reforço

### Satin Denso
- Adiciona pontos ao redor de cada ponto existente
- Cria efeito denso e uniforme
- Ideal para: preenchimentos grandes e sólidos

### Fill Triplo
- Triplica cada ponto com deslocamento
- Aumenta espessura do bordado
- Ideal para: bordados com relevo médio

### Cadeia Grossa
- Adiciona pontos intermediários entre os pontos
- Cria efeito de cadeia grossa
- Ideal para: bordados com textura e movimento

## Formatos Suportados
- **DST**: Tajima (mais comum)
- **PES**: Brother
- **JEF**: Janome
- **EXP**: Melco
- **XXX**: UFAC

## Estrutura do Projeto
- `conversor.py` - Script principal com interface
- `README.md` - Esta documentação
- `testes_novos.py` - Testes das funcionalidades
- `teste_simples.py` - Testes básicos

## Exemplo de Uso
```python
from conversor import ConversorBordado

# Criar instância
conversor = ConversorBordado(root)

# Configurar qualidade
conversor.quality_var.set("Super Alta")

# Ativar reforço
conversor.reinforcement_var.set(True)
conversor.reinforcement_type_var.set("Satin Denso")

# Gerar prévia
conversor.generate_preview()

# Converter e salvar
conversor.convert_image()
```

## Limitações
- Conversão básica (não substitui software profissional)
- Formatos de saída limitados aos principais
- Interface simples sem avanços avançados

## Próximas Melhorias
- Adicionar mais formatos de saída
- Melhorar algoritmo de detecção de bordas
- Adicionar preview 3D do bordado
- Salvar configurações do usuário
- Adicionar undo/redo nas configurações