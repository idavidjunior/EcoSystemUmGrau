# Conversor de Imagem para Bordado

Interface desktop em Python para converter imagens em arquivos de bordado.

## Funcionalidades
- Upload de imagem (JPG, PNG, GIF, BMP)
- Conversão automática para formatos de bordado
- Ajustes manuais (densidade, tipo de costura, largura)
- Exportação nos formatos principais: DST, PES, JEF, EXP, XXX

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
3. Escolher o modo:
   - **Automático**: conversão rápida com configurações padrão
   - **Manual**: ajustar densidade, tipo de costura e largura
4. Selecionar formato de saída (DST, PES, JEF, etc.)
5. Clicar em "Converter e Salvar"
6. Escolher local para salvar o arquivo de bordado

## Formatos Suportados
- **DST**: Tajima (mais comum)
- **PES**: Brother
- **JEF**: Janome
- **EXP**: Melco
- **XXX**: UFAC

## Estrutura do Projeto
- `conversor.py` - Script principal com interface
- `README.md` - Esta documentação
- `teste_simples.py` - Testes de conversão

## Exemplo de Uso
```python
from conversor import ConversorBordado

# Converter imagem automaticamente
conversor = ConversorBordado(root)
conversor.auto_convert(image, pattern)
pyembroidery.write_dst(pattern, "saida.dst")
```

## Limitações
- Conversão básica (não substitui software profissional)
- Formatos de saída limitados aos principais
- Interface simples sem avanços avançados

## Próximas Melhorias
- Adicionar mais formatos de saída
- Melhorar algoritmo de detecção de bordas
- Adicionar preview do resultado
- Salvar configurações do usuário