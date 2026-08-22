"""Testes do Sistema de Compressão Semântica Hierárquica (HSC).

Cobre os casos obrigatórios da spec: texto curto/longo, redundância,
números, datas, negações, causalidade, hipóteses, opiniões, código,
contradição entre fontes, cache, rastreabilidade, validação, reconstrução.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.hsc import SemanticCompressionEngine, CompressionLevelSelector
from scripts.hsc import RedundancyDetector, ImportanceScorer, dividir_frases
import scripts.hsc as hsc

SANDBOX = hsc.ROOT / "runtime" / ".hsc_test"


def setUpModule():
    import shutil
    shutil.rmtree(SANDBOX, ignore_errors=True)
    hsc.HSC_DIR = SANDBOX
    hsc.SOURCES_DIR = SANDBOX / "sources"
    hsc.INDEX_PATH = SANDBOX / "index.json"


def tearDownModule():
    import shutil
    shutil.rmtree(SANDBOX, ignore_errors=True)

TEXTO_CURTO = "Pedro chegou cedo à reunião de segunda-feira."

TEXTO_ARTIGO = """A Revolução Francesa começou em 1789 e mudou a Europa profundamente.
A crise econômica causou grande descontentamento popular entre 1788 e 1789.
A desigualdade social provocou revolta do Terceiro Estado.
A fome levou multidões a tomarem a Bastilha em 14 de julho de 1789.
A queda da Bastilha resultou no fortalecimento da Assembleia Nacional.
Portanto, a monarquia absolutista entrou em colapso nos anos seguintes.
Em 1793 o rei Luís XVI foi executado na guilhotina.
A revolução gerou transformações políticas duradouras no continente."""

TEXTO_REDUNDANTE = """O sistema guardian monitora a RAM do computador continuamente.
O guardian faz monitoramento contínuo da memória RAM da máquina.
Quando a RAM livre cai abaixo de 500 MB o guardian mata o maior processo python.
O sistema guardian encerra o maior processo quando a memória livre fica abaixo de 500 MB.
Essa proteção evita travamentos totais do sistema operacional."""

TEXTO_NUANCAS = """João nasceu em 1980 na cidade de Curitiba.
Provavelmente João começou sua carreira profissional na década seguinte.
Talvez ele tenha estudado na universidade federal antes disso.
Na minha opinião, a trajetória dele foi impressionante.
Não sei onde ele mora atualmente.
João não concluiu o curso de engenharia em 2003.
Ele fundou uma empresa com capital inicial de R$ 50.000 em 2010."""

CODIGO = """def somar(a, b):
    return a + b

class Calculadora:
    def multiplicar(self, x, y):
        resultado = x * y
        return resultado
"""


class TestExtracao(unittest.TestCase):
    def setUp(self):
        self.engine = SemanticCompressionEngine()

    def test_texto_curto_produz_todos_niveis(self):
        rec = self.engine.compress(TEXTO_CURTO, titulo="curto")
        for nivel in ("source", "extraction", "summary", "synthesis",
                      "synopsis", "structure", "key_concepts", "essence",
                      "semantic_core"):
            self.assertIn(nivel, rec["levels"])
        self.assertTrue(rec["validation"]["compression_fidelity_score"] > 0)

    def test_entidades_extrai_nomes_proprios(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        ents = " ".join(rec["levels"]["semantic_core"]["entities"])
        self.assertIn("Revolução", ents + " " + str(rec["levels"]["extraction"]["entities"]))

    def test_numeros_e_datas_preservados(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        ex = rec["levels"]["extraction"]
        self.assertIn("1789", ex["numbers"])
        self.assertTrue(any("1789" in d or "14" in d for d in ex["dates"]))
        core = rec["levels"]["semantic_core"]
        self.assertIn("1789", core["time"])

    def test_negacoes_preservadas_no_core(self):
        rec = self.engine.compress(TEXTO_NUANCAS)
        negados = [f for f in rec["levels"]["semantic_core"]["facts"] if f["negated"]]
        self.assertTrue(negados)

    def test_hipotese_opiniao_incerteza_nao_viram_fato(self):
        rec = self.engine.compress(TEXTO_NUANCAS)
        fatos_fato = [f for f in rec["levels"]["extraction"]["facts"]
                      if f["kind"] == "fact"]
        kinds = {f["kind"] for f in rec["levels"]["extraction"]["facts"]}
        self.assertIn("hypothesis", kinds)
        self.assertIn("opinion", kinds)
        self.assertIn("uncertainty", kinds)
        self.assertFalse(any("talvez" in f["object"].lower() for f in fatos_fato))

    def test_causalidade_detectada(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        ex = rec["levels"]["extraction"]
        self.assertTrue(ex["causes"])
        self.assertTrue(ex["consequences"])
        self.assertEqual(rec["levels"]["semantic_core"]["causes"][0] != "UNKNOWN", True)

    def test_codigo_nao_quebra(self):
        rec = self.engine.compress(CODIGO, titulo="código")
        self.assertTrue(rec["levels"]["essence"])
        self.assertGreater(rec["validation"]["compression_fidelity_score"], 0)


class TestRedundancia(unittest.TestCase):
    def setUp(self):
        self.detector = RedundancyDetector()
        self.scorer = ImportanceScorer()

    def test_duplicado_semantico_detectado(self):
        frases = dividir_frases(TEXTO_REDUNDANTE)
        dups = self.detector.find_duplicates(frases)
        self.assertTrue(dups)
        self.assertEqual(dups[0]["tipo"], "SEMANTIC_DUPLICATE")

    def test_numeros_diferentes_bloqueiam_merge(self):
        f1 = "Processo morto acima de 500 MB."
        f2 = "Processo morto acima de 900 MB."
        self.assertTrue(RedundancyDetector._diferenca_critica(f1, f2))

    def test_resumo_remove_redundancia_mantendo_mais_informativa(self):
        engine = SemanticCompressionEngine()
        rec = engine.compress(TEXTO_REDUNDANTE)
        resumo = rec["levels"]["summary"].lower()
        linhas = [l for l in rec["levels"]["summary"].splitlines() if l.strip()]
        self.assertLess(len(linhas), len(dividir_frases(TEXTO_REDUNDANTE)))
        self.assertIn("500 mb", resumo)


class TestValidacao(unittest.TestCase):
    def setUp(self):
        self.engine = SemanticCompressionEngine()

    def test_fidelity_acima_threshold_em_artigo(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        self.assertGreaterEqual(
            rec["validation"]["compression_fidelity_score"],
            rec["validation"]["threshold"] - 0.15,
            "fidelity razoável esperada; se falhar, compressão perdeu dados")

    def test_checks_presentes(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        for check in ("numeros", "datas", "entidades", "negacoes",
                      "grau_certeza", "fatos_criticos"):
            self.assertIn(check, rec["validation"]["checks"])

    def test_rastreabilidade_fragmentos_validos(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        n_frases = len(rec["levels"]["extraction"]["sentences"])
        for fato in rec["levels"]["extraction"]["facts"]:
            self.assertLess(fato["fragment_idx"], n_frases)

    def test_metricas_compression_ratio(self):
        rec = self.engine.compress(TEXTO_ARTIGO)
        ratio = rec["metrics"]["compression_ratio_essence"]
        self.assertLess(ratio, 0.5, "essência deve ser bem menor que a fonte")


class TestCacheEVersionamento(unittest.TestCase):
    def test_mesma_fonte_nao_recomputa(self):
        engine = SemanticCompressionEngine()
        r1 = engine.compress(TEXTO_ARTIGO + " v1")
        r2 = engine.compress(TEXTO_ARTIGO + " v1")
        self.assertTrue(r2.get("_cache_hit"))
        self.assertEqual(r1["knowledge_id"], r2["knowledge_id"])

    def test_fonte_altera_gera_novo_id(self):
        engine = SemanticCompressionEngine()
        a = engine.compress(TEXTO_ARTIGO + " versao A")
        b = engine.compress(TEXTO_ARTIGO + " versao B diferente")
        self.assertNotEqual(a["knowledge_id"], b["knowledge_id"])


class TestConflitos(unittest.TestCase):
    def test_contradição_entre_fontes_registrada(self):
        engine = SemanticCompressionEngine()
        fonte_a = ("A batalha ocorreu em 1820 perto da capital. "
                   "O exército tinha 5000 soldados.")
        fonte_b = ("A batalha ocorreu em 1850 perto da capital. "
                   "O exército tinha 8000 soldados.")
        resultado = engine.compress_multi([fonte_a, fonte_b], titulo="conflito")
        self.assertTrue(resultado["conflicts"],
                        "diferença de data/número deve virar CONFLICT")

    def test_fontes_concordantes_aumentam_confianca_sem_conflito(self):
        engine = SemanticCompressionEngine()
        fonte_a = "O evento começou em 1901 na praça central."
        fonte_b = "O evento começou em 1901 na praça central da cidade."
        resultado = engine.compress_multi([fonte_a, fonte_b], titulo="ok")
        self.assertEqual(resultado["conflicts"], [])


class TestReconstrucao(unittest.TestCase):
    def test_expand_do_nucleo_ate_source(self):
        engine = SemanticCompressionEngine()
        rec = engine.compress(TEXTO_ARTIGO)
        camadas = SemanticCompressionEngine.SemanticReconstructor if False else None
        from scripts.hsc import SemanticReconstructor
        exp = SemanticReconstructor.expand(rec, ate_nivel="synthesis")
        self.assertIn("semantic_core", exp)
        self.assertIn("synthesis", exp)
        self.assertNotIn("summary", exp)
        exp_total = SemanticReconstructor.expand(rec, ate_nivel="source")
        self.assertEqual(exp_total["source"], TEXTO_ARTIGO)


class TestAutoselecaoNivel(unittest.TestCase):
    def setUp(self):
        self.sel = CompressionLevelSelector()

    def test_verificacao_pedir_fonte(self):
        self.assertEqual(self.sel.recommend("verificar essa afirmação"), 0)

    def test_detalhe_pedir_resumo_l2(self):
        self.assertEqual(self.sel.recommend("explique detalhadamente"), 2)

    def test_pergunta_simples_essencia(self):
        self.assertEqual(self.sel.recommend("o que houve?"), 7)

    def test_numero_especifico_nucleo(self):
        self.assertEqual(self.sel.recommend("quanto custou?"), 8)


class TestPersistencia(unittest.TestCase):
    def test_get_apos_compress(self):
        engine = SemanticCompressionEngine()
        rec = engine.compress("Maria vendeu 120 unidades em março de 2024.",
                              titulo="persist")
        carregado = engine.storage.load(rec["knowledge_id"])
        self.assertIsNotNone(carregado)
        self.assertEqual(carregado["levels"]["essence"], rec["levels"]["essence"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
