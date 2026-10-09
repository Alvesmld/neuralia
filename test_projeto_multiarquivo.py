import json, tempfile, unittest
from pathlib import Path
from projeto_multiarquivo import validar_especificacao, montar

class TestProjetoMultiarquivo(unittest.TestCase):
    def test_valid_spec(self):
        name, files = validar_especificacao({"name":"demo", "files":{"main.py":"print('ok')\n", "docs/LEIA.txt":"oi"}})
        self.assertEqual(name, "demo"); self.assertEqual(len(files), 2)
    def test_traversal_blocked(self):
        with self.assertRaises(ValueError): validar_especificacao({"name":"demo", "files":{"../evil.py":"x=1"}})
    def test_absolute_blocked(self):
        with self.assertRaises(ValueError): validar_especificacao({"name":"demo", "files":{"/tmp/evil.py":"x=1"}})
    def test_bad_syntax(self):
        with self.assertRaises(ValueError): validar_especificacao({"name":"demo", "files":{"main.py":"def x(:\n pass"}})
    def test_bad_name(self):
        with self.assertRaises(ValueError): validar_especificacao({"name":"../bad", "files":{"main.py":"x=1"}})
    def test_create_project(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); spec=root/'spec.json'; spec.write_text(json.dumps({"name":"demo", "files":{"main.py":"x=1\n"}}))
            dest, count=montar(spec, root/'out')
            self.assertEqual(count, 1); self.assertTrue((dest/'main.py').exists())
            with self.assertRaises(FileExistsError): montar(spec, root/'out')
if __name__ == '__main__': unittest.main()
