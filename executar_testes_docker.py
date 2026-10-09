"""Executa testes de um projeto em container Docker restrito (imagem precisa estar local)."""
from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path

RUNNER = r'''import pathlib, shutil, unittest
src = pathlib.Path('/entrada')
dst = pathlib.Path('/tmp/projeto')
shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '.git', 'ALVESMLD_MANIFEST.json'))
import os
os.chdir(dst)
suite = unittest.defaultTestLoader.discover('tests')
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("projeto", help="Pasta do projeto com subpasta tests/")
    p.add_argument("--imagem", default="python:3.12-slim", help="Imagem Docker já baixada")
    p.add_argument("--timeout", type=int, default=60)
    a = p.parse_args()
    project = Path(a.projeto).resolve()
    if not project.is_dir() or not (project / "tests").is_dir():
        p.error("Informe uma pasta existente contendo uma subpasta tests/.")
    if not shutil.which("docker"):
        p.error("Docker não foi encontrado. Instale e inicie o Docker primeiro.")
    check = subprocess.run(["docker", "image", "inspect", a.imagem], capture_output=True, text=True)
    if check.returncode:
        p.error(f"A imagem {a.imagem!r} não está local. Baixe-a manualmente antes de executar.")
    cmd = ["docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", "--pids-limit", "64", "--memory", "256m",
           "--cpus", "1", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--user", "65534:65534",
           "--mount", f"type=bind,src={project},dst=/entrada,readonly", a.imagem,
           "python", "-I", "-c", RUNNER]
    print("Executando dentro do Docker: rede desligada, sistema de arquivos somente leitura e limites de recursos.")
    try:
        result = subprocess.run(cmd, timeout=max(1, min(a.timeout, 300)), check=False)
    except subprocess.TimeoutExpired:
        print("Tempo limite excedido; container encerrado.", file=sys.stderr); raise SystemExit(124)
    raise SystemExit(result.returncode)
if __name__ == "__main__": main()
