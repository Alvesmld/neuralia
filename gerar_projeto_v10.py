"""ALVESMLD v10: planejamento rastreável, testes e memória de resultados.

Não é um LLM geral. Reutiliza os blueprints locais da v9 e acrescenta
rastreamento explícito de requisitos e ciclo de avaliação reproduzível.
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, time
from pathlib import Path
from typing import Any
from gerar_projeto_natural import gerar as gerar_v9, normalizar

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "projetos_gerados"
MEMORIA = ROOT / "memoria_experiencias.jsonl"

# Cada regra vira um requisito verificável; requisitos não implementados ficam
# explicitamente pendentes, em vez de serem declarados como concluídos.
REGRAS = [
    ("interface_grafica", ("interface grafica", "janela", "gui", "visual"), "Criar interface gráfica", "Interface gráfica não é fornecida pelos blueprints de terminal."),
    ("web", ("site", "aplicacao web", "pagina web", "frontend", "html"), "Criar interface web", "Aplicação web não é implementada automaticamente."),
    ("persistencia", ("banco de dados", "sqlite", "persistir", "persistencia", "salvar dados", "armazenar dados"), "Persistir dados", "Persistência não é adicionada automaticamente."),
    ("autenticacao", ("login", "autenticacao", "senha", "usuarios", "usuários"), "Implementar autenticação", "Autenticação requer desenho e testes de segurança específicos."),
    ("exportacao", ("exportar", "csv", "excel", "relatorio", "relatório"), "Exportar dados ou relatórios", "Exportação não é implementada automaticamente."),
    ("rede", ("api", "http", "integracao", "integração", "internet"), "Integrar com API/rede", "Integrações externas não são implementadas automaticamente."),
]

def extrair_requisitos_estruturados(descricao: str) -> list[dict[str, str]]:
    t = normalizar(descricao)
    found = []
    for rid, terms, label, limitation in REGRAS:
        if any(normalizar(term) in t for term in terms):
            found.append({"id": rid, "requisito": label, "status": "pendente", "evidencia": "", "observacao": limitation})
    # Requisitos básicos para sempre haver algo rastreável.
    found.insert(0, {"id": "pedido_original", "requisito": "Preservar e documentar a solicitação original", "status": "incluido", "evidencia": "README.md e PLANO.md", "observacao": "Descrição original armazenada na especificação."})
    found.append({"id": "testes", "requisito": "Gerar testes automatizados do blueprint selecionado", "status": "incluido", "evidencia": "tests/test_app.py", "observacao": "Os testes precisam ser executados para avaliar o comportamento."})
    return found

def salvar_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def executar_testes(projeto: Path, timeout: int = 20) -> dict[str, Any]:
    tests = projeto / "tests"
    if not tests.is_dir():
        return {"status": "sem_testes", "returncode": None, "saida": "Diretório tests/ não encontrado.", "duracao_segundos": 0}
    inicio = time.monotonic()
    try:
        # Não usa shell e executa apenas o conjunto de testes do projeto gerado.
        proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=projeto,
                              capture_output=True, text=True, timeout=timeout, check=False)
        output = (proc.stdout + "\n" + proc.stderr)[-12000:]
        return {"status": "passou" if proc.returncode == 0 else "falhou", "returncode": proc.returncode,
                "saida": output, "duracao_segundos": round(time.monotonic() - inicio, 3)}
    except subprocess.TimeoutExpired as exc:
        return {"status": "timeout", "returncode": None, "saida": str(exc)[:2000], "duracao_segundos": round(time.monotonic() - inicio, 3)}

def avaliar_projeto(projeto: Path, spec: dict[str, Any], teste: dict[str, Any]) -> dict[str, Any]:
    files = [p.relative_to(projeto).as_posix() for p in projeto.rglob("*") if p.is_file()]
    py_files = [p for p in files if p.endswith(".py")]
    matrix = []
    for item in spec["requirements_trace"]:
        row = dict(item)
        if row["id"] == "testes" and "tests/test_app.py" in files:
            row.update(status="incluido", evidencia="tests/test_app.py")
        matrix.append(row)
    included = sum(x["status"] == "incluido" for x in matrix)
    pending = sum(x["status"] == "pendente" for x in matrix)
    return {"projeto": str(projeto), "arquivos": sorted(files), "quantidade_arquivos": len(files),
            "arquivos_python": py_files, "testes": teste, "requisitos": matrix,
            "resumo": {"requisitos_incluidos": included, "requisitos_pendentes": pending,
                       "testes_passaram": teste["status"] == "passou",
                       "aprovado": teste["status"] == "passou" and pending == 0}}

def registrar_experiencia(descricao: str, blueprint: str, resultado: dict[str, Any]) -> None:
    row = {"timestamp": int(time.time()), "descricao": descricao, "blueprint": blueprint,
           "status_testes": resultado["testes"]["status"], "requisitos_pendentes": resultado["resumo"]["requisitos_pendentes"],
           "aprovado": resultado["resumo"]["aprovado"]}
    MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    with MEMORIA.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def gerar_v10(descricao: str, nome: str | None = None, output_root: Path = OUT, rodar_testes: bool = True):
    destino, quantidade, spec = gerar_v9(descricao, nome, output_root)
    trace = extrair_requisitos_estruturados(descricao)
    spec["version"] = 10
    spec["requirements_trace"] = trace
    spec["files"]["MATRIZ_REQUISITOS.md"] = "# Matriz de requisitos\n\n" + "\n".join(
        f"- **{x['status'].upper()}** — {x['requisito']}" + (f" — {x['observacao']}" if x.get("observacao") else "") for x in trace) + "\n"
    spec["files"]["PLANO.md"] += "\n## Rastreamento v10\n\nConsulte MATRIZ_REQUISITOS.md. Requisitos marcados como pendentes não foram implementados automaticamente.\n"
    # Additions after v9's montage are written only to new files in the new destination.
    (destino / "MATRIZ_REQUISITOS.md").write_text(spec["files"]["MATRIZ_REQUISITOS.md"], encoding="utf-8")
    (destino / "PLANO.md").write_text(spec["files"]["PLANO.md"], encoding="utf-8")
    teste = executar_testes(destino) if rodar_testes else {"status": "nao_executado", "returncode": None, "saida": "Execução desativada por opção do usuário.", "duracao_segundos": 0}
    # Remove artefatos transitórios de importação gerados durante unittest.
    import shutil
    for cache in destino.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    resultado = avaliar_projeto(destino, spec, teste)
    salvar_json(destino / "RELATORIO_QUALIDADE.json", resultado)
    registrar_experiencia(descricao, spec.get("blueprint", "desconhecido"), resultado)
    return destino, quantidade + 2, spec, resultado

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("descricao", nargs="?", help="Descrição do projeto")
    p.add_argument("--nome", help="Nome da pasta gerada")
    p.add_argument("--saida", help="Pasta raiz de saída")
    p.add_argument("--sem-testes", action="store_true", help="Não executar os testes do projeto gerado")
    a = p.parse_args()
    descricao = a.descricao or input("Descreva o projeto que deseja criar: ").strip()
    dest, n, spec, result = gerar_v10(descricao, a.nome, Path(a.saida).resolve() if a.saida else OUT, not a.sem_testes)
    print(f"Projeto: {dest}\nBlueprint: {spec.get('blueprint')}\nArquivos criados: {n}")
    print(f"Testes: {result['testes']['status']}\nRequisitos pendentes: {result['resumo']['requisitos_pendentes']}\nAprovado: {result['resumo']['aprovado']}")
    print(f"Relatório: {dest / 'RELATORIO_QUALIDADE.json'}")
    print("Nota: a memória registra resultados; ela não altera automaticamente os pesos do modelo neural.")

if __name__ == "__main__": main()
