// falar-respostas.js — Fala as respostas do assistente via tts_service (EcoSystemUmGrau).
//
// Fluxo: evento message.updated (assistente concluído) -> junta as partes de
// texto da mensagem -> limpa markdown/blocos de código -> grava runtime/
// tts_cmd.json (protocolo oficial do tts_service) -> o serviço único de voz
// fala em fila, respeitando volume e PARAR_FALA globais.
//
// Silêncio controlado pelo botão de voz do Widget Edge: se narracao_estado.json
// tiver ativo=false, nada é falado. Arquivo ausente = fala ligada.

const RUNTIME = "C:/Users/DAVIDJ~1/DOCUME~1/DEFAUL~1/ECOSYS~1/runtime";

async function lerJsonSeguro(caminho) {
  try {
    const fs = await import("node:fs");
    return JSON.parse(fs.readFileSync(caminho, "utf-8"));
  } catch {
    return null;
  }
}

async function enfileirarFala(texto) {
  const fs = await import("node:fs");
  const alvo = `${RUNTIME}/tts_cmd.json`;
  const tmp = `${alvo}.tmp`;
  const carga = JSON.stringify({
    cmd: "speak",
    texto,
    request_id: `${Date.now()}-${Math.floor(Math.random() * 10_000)}`,
    priority: 1,
  });
  fs.writeFileSync(tmp, carga, "utf-8");
  fs.renameSync(tmp, alvo);
}

function limparParaFala(texto) {
  let t = texto || "";
  t = t.replace(/```[\s\S]*?```/g, " bloco de código omitido ");
  t = t.replace(/`([^`]+)`/g, "$1");
  t = t.replace(/^\s{0,3}#{1,6}\s+/gm, "");
  t = t.replace(/\*\*([^*]+)\*\*/g, "$1").replace(/\*([^*]+)\*/g, "$1");
  t = t.replace(/^\s*[-*+]\s+/gm, "");
  t = t.replace(/^\s*>\s?/gm, "");
  t = t.replace(/\|/g, " ");
  t = t
    .replace(/\n{2,}/g, ". ")
    .replace(/\s+\./g, ".")
    .replace(/[ \t]+/g, " ")
    .trim();
  // SEM corte aqui: o SpeechPipeline (SentenceChunker) divide textos longos
  // em chunks de até 2000 chars e concatena o áudio — nada se perde.
  return t;
}

export const FalarRespostas = async () => {
  // partID -> { msgID, texto } (sempre sobrescrito com o texto completo da parte)
  const partes = new Map();
  const faladas = new Set();

  async function falarSePronta(msgID) {
    if (faladas.has(msgID)) return;
    faladas.add(msgID);
    const pedacos = [];
    for (const [id, parte] of [...partes]) {
      if (parte.msgID !== msgID) continue;
      pedacos.push(parte.texto);
      partes.delete(id);
    }
    const texto = limparParaFala(pedacos.join("\n"));
    if (texto.length < 2) return;

    const estado = await lerJsonSeguro(`${RUNTIME}/narracao_estado.json`);
    if (estado && estado.ativo === false) return;

    try {
      await enfileirarFala(texto);
    } catch {
      // fila indisponível: falha silenciosa, nunca derruba a sessão
    }
  }

  return {
    event: async ({ event }) => {
      try {
        if (event.type === "message.part.updated") {
          const p = event.properties?.part;
          if (p && p.type === "text" && p.messageID && p.id) {
            partes.set(p.id, { msgID: p.messageID, texto: p.text || "" });
          }
          return;
        }
        if (event.type === "message.updated") {
          const info = event.properties?.info;
          if (
            info &&
            info.role === "assistant" &&
            info.time?.completed != null &&
            info.id
          ) {
            await falarSePronta(info.id);
          }
        }
      } catch {
        // qualquer erro de formato: ignora o evento, nunca quebra o OpenCode
      }
    },
  };
};

export default FalarRespostas;
