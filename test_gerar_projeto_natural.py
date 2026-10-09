import tempfile, unittest, subprocess, sys
from pathlib import Path
from gerar_projeto_natural import escolher_blueprint, criar_especificacao, gerar

class TestGeradorNatural(unittest.TestCase):
    def test_detecta_calculadora(self):
        self.assertEqual(escolher_blueprint("Faça uma calculadora com soma e divisão"), "calculadora")
    def test_detecta_tarefas(self):
        self.assertEqual(escolher_blueprint("Quero uma lista de tarefas"), "tarefas")
    def test_detecta_rpg(self):
        self.assertEqual(escolher_blueprint("Crie um jogo RPG de texto"), "rpg")
    def test_generico_honesto(self):
        spec = criar_especificacao("Crie uma ferramenta para organizar minhas ideias de estudo")
        self.assertEqual(spec["blueprint"], "generico")
        self.assertIn("não são simulados", " ".join(spec["requirements"]))
    def test_recusa_descricao_curta(self):
        with self.assertRaises(ValueError): criar_especificacao("oi")
    def test_recusa_descricao_enorme(self):
        with self.assertRaises(ValueError): criar_especificacao("x" * 5001)
    def test_cria_projeto_com_testes(self):
        with tempfile.TemporaryDirectory() as td:
            dest, count, spec = gerar("Crie uma calculadora", "calc", Path(td))
            self.assertTrue((dest / "app.py").exists())
            self.assertTrue((dest / "tests/test_app.py").exists())
            self.assertEqual(spec["blueprint"], "calculadora")
            self.assertGreaterEqual(count, 4)
            result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=dest, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    def test_nao_sobrescreve_destino(self):
        with tempfile.TemporaryDirectory() as td:
            gerar("Crie uma calculadora", "calc", Path(td))
            with self.assertRaises(FileExistsError): gerar("Crie uma calculadora", "calc", Path(td))

if __name__ == "__main__": unittest.main()
