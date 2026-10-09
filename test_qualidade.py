import unittest
from codegen.qualidade import validar_python
from gerenciar_dataset import auditar
from pathlib import Path
import tempfile, json

class QualidadeTests(unittest.TestCase):
    def test_codigo_valido(self):
        self.assertTrue(validar_python('def soma(a, b):\n    return a + b').valido)
    def test_codigo_invalido(self):
        r = validar_python('def soma(:')
        self.assertFalse(r.valido)
        self.assertIsNotNone(r.linha)
    def test_codigo_vazio(self):
        self.assertFalse(validar_python('  ').valido)
    def test_dataset_remove_duplicata(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'dados.jsonl'
            item = {"instruction":"somar", "code":"def soma(a,b): return a+b"}
            p.write_text(json.dumps(item)+'\n'+json.dumps(item)+'\n', encoding='utf-8')
            r = auditar(p)
            self.assertEqual(r['registros_validos_unicos'], 1)
            self.assertEqual(r['duplicados'], 1)
    def test_dataset_rejeita_campos_vazios(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'dados.jsonl'
            p.write_text('{"instruction":"", "code":"x=1"}\n', encoding='utf-8')
            self.assertEqual(len(auditar(p)['erros']), 1)
if __name__ == '__main__': unittest.main()
