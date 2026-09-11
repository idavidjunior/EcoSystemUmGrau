# Conversor de Imagem para Bordado

Interface desktop em Python para converter imagens em arquivos de bordado.

## Funcionalidades
- Upload de imagem (JPG, PNG, GIF)
- Conversão automática para formatos de bordado
- Ajustes manuais (densidade, tipo de costura, cores)
- Exportação nos formatos principais: DST, PES, JEF

## Tecnologias
- Python 3
- tkinter (interface desktop)
- pyembroidery (motor de conversão)
- Pillow (processamento de imagem)

## Como usar
1. Instalar dependências: `pip install pyembroidery pillow`
2. Executar: `python conversor.py`
3. Selecionar imagem
4. Ajustar configurações (modo manual) ou usar automático
5. Exportar arquivo de bordado

## Estrutura
- `conversor.py` - Script principal com interface
- `README.md` - Esta documentação