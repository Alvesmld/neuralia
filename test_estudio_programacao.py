import tempfile, unittest
from pathlib import Path
import estudio_programacao as ep

class StudioTests(unittest.TestCase):
    def test_plano_detecta_capacidades(self):
        p=ep.inferir_plano('crie um cadastro de contatos com janela visual, salvar e testes')
        self.assertEqual(p['linguagem'],'Python'); self.assertEqual(p['interface'],'gui')
        self.assertTrue(p['persistencia']); self.assertTrue(p['crud']); self.assertTrue(p['testes'])
    def test_diferentes_arquiteturas(self):
        self.assertIn('index.html', ep.gerar_web(ep.inferir_plano('site web')))
        self.assertIn('app.py', ep.gerar_api())
        self.assertIn('lib/main.dart', ep.gerar_flutter())
    def test_python_sintaxe(self):
        for plano in [ep.inferir_plano('app python'), ep.inferir_plano('cadastro visual salvar testes')]:
            for nome, codigo in ep.gerar_python(plano).items():
                if nome.endswith('.py'): compile(codigo,nome,'exec')
    def test_compose_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo=Path(tmp)/'demo'; alvo.mkdir()
            files=ep.compor_projeto(alvo, ep.inferir_plano('cadastro de tarefas salvar e testes'))
            self.assertIn('main.py',files); self.assertTrue((alvo/'core.py').exists()); self.assertTrue((alvo/'test_core.py').exists())

if __name__=='__main__': unittest.main()
