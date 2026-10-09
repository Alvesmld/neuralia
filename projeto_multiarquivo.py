"""Monta projetos Python com vários arquivos a partir de uma especificação JSON."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "projetos_gerados"
MAX_FILES = 100
MAX_FILE_BYTES = 1_000_000

def validar_especificacao(obj):
    if not isinstance(obj, dict) or not isinstance(obj.get("files"), dict):
        raise ValueError("JSON precisa conter um objeto 'files' com caminhos e conteúdos.")
    name = obj.get("name", "projeto")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", name):
        raise ValueError("'name' deve conter apenas letras, números, '_' ou '-' (até 60 caracteres).")
    files = obj["files"]
    if not files or len(files) > MAX_FILES:
        raise ValueError(f"Informe entre 1 e {MAX_FILES} arquivos.")
    normalized = {}
    for raw, content in files.items():
        if not isinstance(raw, str) or not isinstance(content, str):
            raise ValueError("Cada caminho e conteúdo deve ser texto.")
        p = PurePosixPath(raw)
        if p.is_absolute() or not p.parts or any(part in ("..", ".") for part in p.parts) or "\\" in raw:
            raise ValueError(f"Caminho inseguro recusado: {raw!r}")
        if any(part.startswith(".") for part in p.parts):
            raise ValueError(f"Arquivos/pastas ocultos não são aceitos: {raw!r}")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValueError(f"Arquivo muito grande: {raw}")
        if p.suffix == ".py":
            try: ast.parse(content, filename=raw)
            except SyntaxError as e: raise ValueError(f"Sintaxe inválida em {raw}, linha {e.lineno}: {e.msg}") from e
        normalized[p.as_posix()] = content
    return name, normalized

def montar(spec_path: Path, output_root: Path = OUT):
    obj = json.loads(spec_path.read_text(encoding="utf-8"))
    name, files = validar_especificacao(obj)
    destination = output_root / name
    if destination.exists():
        raise FileExistsError(f"Destino já existe; nada foi sobrescrito: {destination}")
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for rel, content in files.items():
            target = destination.joinpath(*PurePosixPath(rel).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (destination / "ALVESMLD_MANIFEST.json").write_text(json.dumps({"name": name, "files": list(files)}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        import shutil; shutil.rmtree(destination, ignore_errors=True); raise
    return destination, len(files)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("especificacao", help="Arquivo JSON com name e files")
    p.add_argument("--saida", help="Pasta raiz de saída (padrão: projetos_gerados)")
    a = p.parse_args()
    dest, count = montar(Path(a.especificacao).resolve(), Path(a.saida).resolve() if a.saida else OUT)
    print(f"Projeto criado: {dest}\nArquivos: {count}\nSintaxe Python: validada nos arquivos .py encontrados.")
    print("A validação sintática não garante que o programa funcione ou seja seguro.")
if __name__ == "__main__": main()
