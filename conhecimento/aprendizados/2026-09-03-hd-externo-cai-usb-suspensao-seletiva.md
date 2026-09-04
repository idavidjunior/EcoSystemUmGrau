---
tipo: episodio
tags: [hardware, hd-externo, usb, energia, diagnostico]
data: 2026-09-03
contexto: O usuário relatou que o HD externo cai e some esporadicamente, obrigando desconectar e reconectar o cabo USB para o PC reconhecer novamente.
decisao: Diagnosticado via Get-PnpDevice, powercfg e Event Log. Causa de software corrigida: suspensão seletiva USB estava ATIVADA (AC e DC). Desabilitada via powercfg (indice 0). Causas físicas apontadas mas não resolvidas.
impacto: Redução da causa mais provável de queda USB por software. Causas físicas (cabo frágil, energia da porta, ponte USB do SSD) permanecem em aberto.
---

# HD externo cai e some esporadicamente

## Sintoma
O HD externo (SSD portátil USB, marca genérica "AL") some do PC de vez em quando e só volta depois de desconectar e reconectar o cabo USB.

## Diagnóstico realizado
- Disco identificado: `AL SSD USB Device` (USBSTOR). Duas instâncias: uma OK (ativa) e outra Unknown (inativa/desconectada) — confirma desconexão na camada USB.
- Plano de energia: Desempenho Máximo. Disco não desliga por idle (DISKIDLE=0). Isso descarta causa "economia de energia de disco".
- Suspensão seletiva USB: estava ATIVADA (indice 1) tanto em AC quanto em DC. É a causa clássica de USB "sumir" e precisar reconectar.
- Event Log (Id 51, erro de I/O de disco): a última rajada foi em 30/08/2026 23:04 (vários erros no mesmo minuto) — episódio isolado, não quedas diárias. Indica que também há componente de falha real de I/O (cabo/energia/firmware), não só software.

## Correção aplicada (software)
Desabilitada a suspensão seletiva USB no esquema corrente, em AC e DC:
- `powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0`
- `powercfg /setdcvalueindex SCHEME_CURRENT ... 0`
- `powercfg /setactive SCHEME_CURRENT`

Confirmado: agora `Indice de Correntes Alternadas Atuais / Continuas = 0x00000000` (Desabilitado).

## Próximos passos (causas físicas, não resolvidas por software) — recomendação ao usuário
1. Trocar o cabo USB (cabos de SSD portátil baratos são frágeis e a causa mais comum).
2. Conectar direto na porta USB do PC (preferência porta traseira/3.x), evitar hub USB sem fonte própria.
3. Se persistir, testar em outra porta USB para descartar porta com pouca energia.
4. Observar se as quedas acontecem sob transferência pesada (esquenta/corrente) — pode indicar ponte SATA-USB do SSD com defeito térmico.
