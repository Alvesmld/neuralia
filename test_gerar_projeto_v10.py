import json
import tempfile
import unittest
from pathlib import Path
from gerar_projeto_v10 import extrair_requisitos_estruturados, avaliar_projeto, executar_testes

class TestPlanejadorV10(unittest.TestCase):
    def test_detecta_requisitos_nao_implementados(self):
        rows = extrair_requisitos_estruturados("Crie um site com login e banco de dados SQLite")
        ids = {r["id"] for r in rows}
        self.assertTrue({"web", "autenticacao", "persistencia"}.issubset(ids))
        self.assertTrue(all(r["status"] == "pendente" for r in rows if r["id"] in {"web", "autenticacao", "persistencia"}))

    def test_inclui_matriz_basica(self):
        rows = extrair_requisitos_estruturados("Crie uma calculadora simples")
        self.assertEqual(rows[0]["id"], "pedido_original")
        self.assertTrue(any(r["id"] == "testes" for r in rows))

    def test_executa_testes_de_projeto_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests" / "test_ok.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertEqual(2+2,4)\n")
            result = executar_testes(root)
            self.assertEqual(result["status"], "passou", result["saida"])

    def test_timeout_e_resultado_valido(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = executar_testes(root)
            self.assertEqual(result["status"], "sem_testes")

if __name__ == "__main__": unittest.main()
