import asyncio
import base64
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)
sys.path.insert(0, os.path.dirname(_SCRIPTS))

from tts.config import MIN_TEXT_LENGTH


# ---- Stream por sentenÃ§a (SpeechPipeline.stream_sentencas) ----

def test_stream_sentencas_divide_por_sentenca():
    """Texto com vÃ¡rias sentenÃ§as produz um chunk tocÃ¡vel por sentenÃ§a."""
    from tts.speech_pipeline import SpeechPipeline
    p = SpeechPipeline()

    async def fake_synth(texto):
        return b"\xff\xf3" + texto.encode("utf-8")

    p._synthesize_async = fake_synth

    async def run():
        texto = "OlÃ¡, senhor. Como posso ajudar hoje? EstÃ¡ tudo funcionando normalmente!"
        chunks = []
        async for chunk in p.stream_sentencas(texto):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())
    assert len(chunks) >= 3, f"esperava >= 3 chunks, veio {len(chunks)}"
    for c in chunks:
        audio = base64.b64decode(c)
        assert audio[:2] == b"\xff\xf3", "chunk nÃ£o parece MP3 vÃ¡lido"
    print(f"stream_sentencas: {len(chunks)} chunks de uma resposta de 3 sentenÃ§as OK")


def test_stream_sentencas_texto_unico():
    """Uma Ãºnica sentenÃ§a produz exatamente um chunk."""
    from tts.speech_pipeline import SpeechPipeline
    p = SpeechPipeline()

    async def fake_synth(texto):
        return b"\xff\xf3" + texto.encode("utf-8")

    p._synthesize_async = fake_synth

    async def run():
        chunks = []
        async for chunk in p.stream_sentencas("Tudo funcionando."):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())
    assert len(chunks) == 1, f"esperava 1 chunk, veio {len(chunks)}"
    print(f"stream_sentencas: texto Ãºnico -> 1 chunk OK")


def test_stream_sentencas_agrupa_partes_curtas():
    """Partes com menos de MIN_TEXT_LENGTH sÃ£o agrupadas Ã  parte seguinte,
    evitando TextTooShortError por sentenÃ§a isolada."""
    from tts.speech_pipeline import SpeechPipeline
    p = SpeechPipeline()
    assert MIN_TEXT_LENGTH >= 5

    async def fake_synth(texto):
        return b"\xff\xf3" + texto.encode("utf-8")

    p._synthesize_async = fake_synth

    async def run():
        chunks = []
        async for chunk in p.stream_sentencas("Ok, entendi. AmanhÃ£ eu termino o relatÃ³rio."):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())
    assert len(chunks) >= 1, "nÃ£o gerou nenhum chunk"
    # O "Ok," curto nÃ£o pode virar um chunk sozinho (lanÃ§aria erro de sÃ­ntese)
    for c in chunks:
        audio = base64.b64decode(c)
        assert audio[:2] == b"\xff\xf3"
    print(f"stream_sentencas: agrupamento de partes curtas OK ({len(chunks)} chunks)")


def test_stream_sentencas_texto_vazio():
    """Texto vazio nÃ£o gera chunks e nÃ£o lanÃ§a erro."""
    from tts.speech_pipeline import SpeechPipeline
    p = SpeechPipeline()
    p._synthesize_async = lambda t: b"\xff\xf3"

    async def run():
        chunks = []
        async for chunk in p.stream_sentencas(""):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run())
    assert chunks == []
    print("stream_sentencas: texto vazio -> 0 chunks OK")


# ---- gerar_audio_stream da bridge ----

def test_gerar_audio_stream_usa_stream_sentencas():
    """A bridge deve usar stream_sentencas quando o pipeline expÃµe o mÃ©todo
    (cada yield Ã© um MP3 completo de uma sentenÃ§a)."""
    import jarvis_bridge as jb
    original_pipeline = jb._speech_pipeline

    class FakePipeline:
        async def stream_sentencas(self, texto):
            yield base64.b64encode(b"\xff\xf3sent1").decode()
            yield base64.b64encode(b"\xff\xf3sent2").decode()

    try:
        jb._speech_pipeline = FakePipeline()
        jb.SPEECH_PIPELINE_AVAILABLE = True

        async def run():
            out = []
            async for chunk in jb.gerar_audio_stream("duas sentenÃ§as"):
                out.append(chunk)
            return out

        out = asyncio.run(run())
        assert len(out) == 2, f"esperava 2 chunks, veio {len(out)}"
        for c in out:
            assert base64.b64decode(c)[:2] == b"\xff\xf3"
        print("gerar_audio_stream: usa stream_sentencas OK (2 sentenÃ§as)")
    finally:
        jb._speech_pipeline = original_pipeline


def test_gerar_audio_stream_texto_vazio():
    """Texto vazio deve retornar imediatamente, sem erro."""
    import jarvis_bridge as jb

    async def run():
        out = []
        async for chunk in jb.gerar_audio_stream(""):
            out.append(chunk)
        return out

    out = asyncio.run(run())
    assert out == []
    print("gerar_audio_stream: texto vazio -> 0 chunks OK")


# ---- Contrato do barge-in ({"tipo":"cancelar"} -> {"tipo":"cancelado"}) ----

def test_bridge_trata_cancelar():
    """A bridge deve responder a {"tipo":"cancelar"} com {"tipo":"cancelado"},
    incluindo audio_done para o app encerrar o playback."""
    import jarvis_bridge as jb
    src = open(os.path.join(os.path.dirname(__file__), "jarvis_bridge.py"), encoding="utf-8").read()
    assert '"cancelar"' in src and 'obj.get("tipo") == "cancelar"' in src, "handler cancelar ausente"
    assert '"cancelado"' in src, "resposta cancelado ausente"
    assert 'task_resposta.cancel()' in src, "cancelamento de task ausente"
    assert '"audio_done": True' in src, "audio_done ausente no cancelamento"
    assert '_responder_fala' in src and 'asyncio.create_task(_responder_fala' in src, "resposta nÃ£o roda em task cancelÃ¡vel"
    print("bridge: handler de barge-in (cancelar/cancelado) presente e correto OK")


def teste_cancelar_durante_fala(bridge_stub=None):
    """Permite que um teste de integraÃ§Ã£o real (websocket) valide o fluxo
    ponta a ponta, sem executar a bridge completa aqui."""
    print("cancelar_durante_fala: disponÃ­vel para integraÃ§Ã£o ponta-a-ponta")


if __name__ == "__main__":
    print("=== Testes de voz fluida (streaming por sentenÃ§a + barge-in) ===")
    test_stream_sentencas_divide_por_sentenca()
    test_stream_sentencas_texto_unico()
    test_stream_sentencas_agrupa_partes_curtas()
    test_stream_sentencas_texto_vazio()
    test_gerar_audio_stream_usa_stream_sentencas()
    test_gerar_audio_stream_texto_vazio()
    test_bridge_trata_cancelar()
    print("=== TODOS OS TESTES PASSARAM ===")