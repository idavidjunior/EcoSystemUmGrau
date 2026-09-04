import json
import subprocess
import unittest
from unittest.mock import patch

try:
    from scripts.runtime_kernel import Kernel
except ModuleNotFoundError:
    from runtime_kernel import Kernel


class RuntimeKernelTests(unittest.TestCase):
    def setUp(self):
        self.kernel = Kernel()

    def test_carrega_regras_da_constituicao(self):
        self.assertGreaterEqual(len(self.kernel.rules), 7)

    def test_autorizacao_inclui_contexto_relevante(self):
        contexto = {
            'projeto_ativo': 'ProjetoTeste',
            'memorias': [{'titulo': 'memoria teste'}],
            'conhecimento': [{'titulo': 'conhecimento teste'}],
            'decisoes': [{'titulo': 'decisão teste'}],
        }
        with patch.object(self.kernel, '_load_task_context', return_value=contexto):
            contrato = self.kernel.authorize('teste')

        self.assertIs(contrato['contexto_relevante'], contexto)
        self.assertEqual(contrato['memoria_necessaria'], ['memoria teste'])
        self.assertEqual(contrato['ferramentas'], ['conhecimento teste'])
        self.assertIn('ProjetoTeste', contrato['contexto'])

    def test_parser_aceita_payload_direto_do_planner(self):
        response = {'goal': 'teste', 'steps': []}

        self.assertEqual(self.kernel._parse_mcp_response(response), response)

    def test_parser_aceita_envelope_jsonrpc(self):
        payload = {'goal': 'teste', 'steps': []}
        response = {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': json.dumps(payload)}]},
        }

        self.assertEqual(self.kernel._parse_mcp_response(response), payload)

    @patch('scripts.runtime_kernel.subprocess.run')
    def test_executor_propagates_falha_do_subprocesso(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout='', stderr='falha de teste'
        )

        result = self.kernel._execute_plan_via_orchestrator({'steps': []}, 'teste')

        self.assertIn('error', result)
        self.assertIn('falhou', result['error'])

    def test_gate_bloqueia_se_compreensao_indisponivel(self):
        with patch.object(self.kernel, '_load_compreensao_mod', return_value=None):
            result = self.kernel.gate_veto('teste')

        self.assertFalse(result['aprovado'])
        self.assertEqual(result['status'], 'BLOQUEADO')

    def test_directo_identifica_pedido_sem_ferramenta(self):
        result = self.kernel._execute_direct(
            'qual a data de hoje', {'objetivo': 'qual a data de hoje'}
        )

        self.assertEqual(result['status'], 'needs_response')

    def test_selecao_direct_de_lista_de_arquivos(self):
        selected = self.kernel._select_direct_tool(
            'liste arquivos da pasta atual', {'requires_tools': True}
        )

        self.assertEqual(selected, ('FileAgent', 'list_files', 'mcp-dev-tools'))

    def test_selecao_direct_recusa_pedido_sem_ferramenta_conhecida(self):
        selected = self.kernel._select_direct_tool(
            'consulte uma API externa de clima', {'requires_tools': True}
        )

        self.assertIsNone(selected)

    @patch('scripts.runtime_kernel.Kernel._execute_direct')
    def test_execute_plan_delega_rota_direct(self, execute_direct):
        execute_direct.return_value = {'route': 'DIRECT', 'status': 'success'}

        with patch.object(self.kernel, 'route_task', return_value={
            'route': 'DIRECT',
            'contract': {'objetivo': 'teste'},
        }):
            result = self.kernel.execute_plan('teste')

        execute_direct.assert_called_once_with('teste', {'objetivo': 'teste'})
        self.assertEqual(result['status'], 'success')


if __name__ == '__main__':
    unittest.main()