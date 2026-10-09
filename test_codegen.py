import json, tempfile, unittest
from pathlib import Path
from codegen.modelo import formatar_exemplo, carregar_corpus

class CodegenTests(unittest.TestCase):
    def test_formato_exemplo(self):
        texto=formatar_exemplo("somar dois números", "def somar(a, b):\n    return a+b")
        self.assertIn("### INSTRUÇÃO",texto)
        self.assertIn("### CÓDIGO",texto)
        self.assertIn("### FIM",texto)
    def test_carregar_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"data.jsonl"
            p.write_text(json.dumps({"instruction":"teste","code":"x = 1"})+"\n",encoding="utf-8")
            self.assertEqual(len(carregar_corpus(p)),1)
    def test_rejeita_linha_invalida(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"data.jsonl"; p.write_text("{invalido}\\n",encoding="utf-8")
            with self.assertRaises(ValueError): carregar_corpus(p)
    def test_corpus_inicial_tem_exemplos(self):
        from codegen.modelo import DEFAULT_DATASET
        self.assertGreaterEqual(len(carregar_corpus(DEFAULT_DATASET)),20)
if __name__=="__main__": unittest.main()
