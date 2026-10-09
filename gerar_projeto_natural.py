"""Planeja e monta projetos Python a partir de descrições em linguagem natural.

A v9 usa planejamento por regras e blueprints verificáveis, não um LLM geral.
"""
from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path
from projeto_multiarquivo import validar_especificacao, montar

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "projetos_gerados"


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def slug(texto: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", normalizar(texto)).strip("_-")
    return (s[:50] or "projeto_alvesmld").lower()


def escolher_blueprint(descricao: str) -> str:
    t = normalizar(descricao)
    if any(x in t for x in ("calculadora", "somar", "calcular media", "fatorial")):
        return "calculadora"
    if any(x in t for x in ("lista de tarefas", "tarefas", "todo", "to-do", "afazeres")):
        return "tarefas"
    if any(x in t for x in ("rpg", "jogo de texto", "aventura", "combate por turno")):
        return "rpg"
    return "generico"


def extrair_requisitos(descricao: str) -> list[str]:
    t = normalizar(descricao)
    requisitos = []
    regras = [
        (("banco de dados", "sqlite", "salvar dados", "persistencia"), "Persistência de dados: identificar armazenamento adequado; o blueprint atual não adiciona banco automaticamente."),
        (("interface grafica", "interface visual", "janela", "gui"), "Interface gráfica solicitada: o blueprint atual é de terminal e precisa de implementação visual específica."),
        (("web", "site", "pagina", "html", "frontend"), "Interface web solicitada: não incluída automaticamente pelo blueprint de terminal."),
        (("login", "autenticacao", "senha", "usuarios"), "Autenticação mencionada: requer desenho de segurança específico e não será simulada como pronta."),
        (("teste", "testes", "pytest", "unittest"), "Testes automatizados incluídos quando compatíveis com o blueprint."),
    ]
    for palavras, msg in regras:
        if any(p in t for p in palavras): requisitos.append(msg)
    if not requisitos:
        requisitos.append("Descrição analisada; confirme os requisitos específicos antes de considerar o projeto completo.")
    requisitos.append("Implementação automática limitada aos blueprints disponíveis; requisitos fora deles não são simulados como concluídos.")
    return requisitos


def arquivos_blueprint(tipo: str, descricao: str) -> dict[str, str]:
    common_readme = f"# Projeto gerado pelo ALVESMLD v9\n\n## Solicitação original\n\n{descricao}\n\n## Executar\n\n```bash\npython app.py\n```\n\n## Testes\n\n```bash\npython -m unittest discover -s tests -v\n```\n\nEste projeto foi criado por um blueprint local. Revise os requisitos e o código antes de usar.\n"
    if tipo == "calculadora":
        app = '''"""Calculadora simples para terminal."""\n\ndef somar(a: float, b: float) -> float:\n    return a + b\n\ndef subtrair(a: float, b: float) -> float:\n    return a - b\n\ndef multiplicar(a: float, b: float) -> float:\n    return a * b\n\ndef dividir(a: float, b: float) -> float:\n    if b == 0:\n        raise ValueError("Não é possível dividir por zero.")\n    return a / b\n\ndef main() -> None:\n    print("ALVESMLD Calculadora — escolha uma operação")\n    print("Operações disponíveis: +, -, *, /")\n    try:\n        a = float(input("Primeiro número: "))\n        op = input("Operação: ").strip()\n        b = float(input("Segundo número: "))\n        funcs = {"+": somar, "-": subtrair, "*": multiplicar, "/": dividir}\n        if op not in funcs:\n            print("Operação desconhecida.")\n            return\n        print("Resultado:", funcs[op](a, b))\n    except (ValueError, EOFError) as exc:\n        print("Entrada inválida:", exc)\n\nif __name__ == "__main__":\n    main()\n'''
        tests = '''import unittest\nfrom app import somar, subtrair, multiplicar, dividir\n\nclass TestCalculadora(unittest.TestCase):\n    def test_operacoes(self):\n        self.assertEqual(somar(2, 3), 5)\n        self.assertEqual(subtrair(5, 2), 3)\n        self.assertEqual(multiplicar(3, 4), 12)\n        self.assertEqual(dividir(8, 2), 4)\n    def test_divisao_por_zero(self):\n        with self.assertRaises(ValueError):\n            dividir(1, 0)\n\nif __name__ == "__main__": unittest.main()\n'''
    elif tipo == "tarefas":
        app = '''"""Lista de tarefas em memória, executada no terminal."""\n\ndef listar(tarefas: list[str]) -> list[str]:\n    return list(tarefas)\n\ndef adicionar(tarefas: list[str], texto: str) -> None:\n    texto = texto.strip()\n    if not texto:\n        raise ValueError("A tarefa não pode ficar vazia.")\n    tarefas.append(texto)\n\ndef remover(tarefas: list[str], indice: int) -> str:\n    if indice < 0 or indice >= len(tarefas):\n        raise IndexError("Número de tarefa inválido.")\n    return tarefas.pop(indice)\n\ndef main() -> None:\n    tarefas: list[str] = []\n    while True:\n        print("\\n1. Listar  2. Adicionar  3. Remover  0. Sair")\n        escolha = input("> ").strip()\n        if escolha == "0": break\n        try:\n            if escolha == "1":\n                for i, tarefa in enumerate(listar(tarefas), 1): print(f"{i}. {tarefa}")\n            elif escolha == "2": adicionar(tarefas, input("Nova tarefa: "))\n            elif escolha == "3": print("Removida:", remover(tarefas, int(input("Número: ")) - 1))\n            else: print("Opção desconhecida.")\n        except (ValueError, IndexError) as exc: print("Erro:", exc)\n\nif __name__ == "__main__":\n    main()\n'''
        tests = '''import unittest\nfrom app import adicionar, listar, remover\n\nclass TestTarefas(unittest.TestCase):\n    def test_adicionar_listar_remover(self):\n        itens = []\n        adicionar(itens, "Estudar Python")\n        self.assertEqual(listar(itens), ["Estudar Python"])\n        self.assertEqual(remover(itens, 0), "Estudar Python")\n        self.assertEqual(itens, [])\n    def test_vazia_recusada(self):\n        with self.assertRaises(ValueError): adicionar([], " ")\n\nif __name__ == "__main__": unittest.main()\n'''
    elif tipo == "rpg":
        app = '''"""Mini RPG de terminal com combate simples por turnos."""\nfrom dataclasses import dataclass\n\n@dataclass\nclass Personagem:\n    nome: str\n    vida: int = 30\n    ataque: int = 7\n\ndef atacar(atacante: Personagem, alvo: Personagem) -> int:\n    dano = max(1, atacante.ataque)\n    alvo.vida = max(0, alvo.vida - dano)\n    return dano\n\ndef main() -> None:\n    heroi = Personagem("Aventureiro", 30, 8)\n    inimigo = Personagem("Slime", 18, 4)\n    print("ALVESMLD RPG — encontre a saída da caverna!")\n    while heroi.vida > 0 and inimigo.vida > 0:\n        input("Pressione Enter para atacar...")\n        print(f"Você causa {atacar(heroi, inimigo)} de dano. Vida do inimigo: {inimigo.vida}")\n        if inimigo.vida > 0:\n            print(f"O inimigo causa {atacar(inimigo, heroi)} de dano. Sua vida: {heroi.vida}")\n    print("Vitória!" if heroi.vida > 0 else "Você foi derrotado.")\n\nif __name__ == "__main__":\n    main()\n'''
        tests = '''import unittest\nfrom app import Personagem, atacar\n\nclass TestRPG(unittest.TestCase):\n    def test_ataque_reduz_vida(self):\n        a, b = Personagem("A", 20, 5), Personagem("B", 10, 3)\n        self.assertEqual(atacar(a, b), 5)\n        self.assertEqual(b.vida, 5)\n    def test_vida_nao_fica_negativa(self):\n        a, b = Personagem("A", 20, 50), Personagem("B", 3, 1)\n        atacar(a, b)\n        self.assertEqual(b.vida, 0)\n\nif __name__ == "__main__": unittest.main()\n'''
    else:
        app = f'''"""Ponto de partida honesto para um projeto descrito em linguagem natural."""\nDESCRICAO_ORIGINAL = {descricao!r}\n\ndef mostrar_plano() -> None:\n    print("Projeto ALVESMLD criado a partir da descrição:")\n    print(DESCRICAO_ORIGINAL)\n    print("\\nEste é um scaffold inicial, não uma implementação completa dos requisitos.")\n    print("Edite app.py e acrescente módulos e testes conforme o plano em PLANO.md.")\n\nif __name__ == "__main__":\n    mostrar_plano()\n'''
        tests = '''import unittest\nfrom app import DESCRICAO_ORIGINAL\n\nclass TestProjeto(unittest.TestCase):\n    def test_descricao_preservada(self):\n        self.assertTrue(DESCRICAO_ORIGINAL.strip())\n\nif __name__ == "__main__": unittest.main()\n'''
    plan = "# Plano de implementação\n\n## Descrição original\n\n" + descricao + "\n\n## Requisitos detectados / alertas\n\n" + "\n".join(f"- {x}" for x in extrair_requisitos(descricao)) + "\n\n## Próximas etapas sugeridas\n\n- Confirmar entradas, saídas e regras de negócio.\n- Implementar requisitos que ainda não estejam no blueprint.\n- Executar os testes e revisar o comportamento.\n- Revisar segurança antes de usar dados reais.\n"
    return {"app.py": app, "tests/test_app.py": tests, "README.md": common_readme, "PLANO.md": plan}


def criar_especificacao(descricao: str, nome: str | None = None) -> dict:
    if not isinstance(descricao, str) or len(descricao.strip()) < 8:
        raise ValueError("Descreva o projeto com pelo menos 8 caracteres.")
    if len(descricao) > 5000:
        raise ValueError("A descrição deve ter no máximo 5000 caracteres.")
    tipo = escolher_blueprint(descricao)
    nome_final = slug(nome or ("projeto_" + tipo if tipo != "generico" else "projeto_personalizado"))
    spec = {"name": nome_final, "description": descricao, "blueprint": tipo, "requirements": extrair_requisitos(descricao), "files": arquivos_blueprint(tipo, descricao)}
    validar_especificacao(spec)
    return spec


def gerar(descricao: str, nome: str | None = None, output_root: Path = OUT, salvar_spec: bool = True):
    spec = criar_especificacao(descricao, nome)
    output_root.mkdir(parents=True, exist_ok=True)
    spec_path = output_root / (spec["name"] + "_spec.json")
    if (output_root / spec["name"]).exists():
        raise FileExistsError(f"Destino já existe; nada foi sobrescrito: {output_root / spec['name']}")
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    destino, quantidade = montar(spec_path, output_root)
    if not salvar_spec:
        spec_path.unlink(missing_ok=True)
    return destino, quantidade, spec


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("descricao", nargs="?", help="Descreva o programa que deseja criar")
    p.add_argument("--nome", help="Nome da pasta/projeto")
    p.add_argument("--saida", help="Pasta de destino")
    p.add_argument("--listar-blueprints", action="store_true")
    a = p.parse_args()
    if a.listar_blueprints:
        print("calculadora\ntarefas\nrpg\ngenerico")
        return
    descricao = a.descricao or input("Descreva o projeto que deseja criar: ").strip()
    dest, n, spec = gerar(descricao, a.nome, Path(a.saida).resolve() if a.saida else OUT)
    print(f"Blueprint selecionado: {spec['blueprint']}\nProjeto criado: {dest}\nArquivos: {n}")
    print("\nAtenção: a seleção é baseada em regras e modelos reutilizáveis, não em compreensão geral por um grande modelo neural.")
    print("Consulte PLANO.md e execute os testes do projeto gerado antes de usar.")

if __name__ == "__main__": main()
