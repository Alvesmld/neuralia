"""API web da ALVESMLD v11. Não executa os testes dos projetos enviados pela web."""
from __future__ import annotations
import os, re, shutil, time, uuid
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from gerar_projeto_v10 import gerar_v10
from gerar_projeto_natural import slug

ROOT = Path(__file__).resolve().parent
OUT = (ROOT / "projetos_web").resolve()
OUT.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="ALVESMLD API", version="11.0.0", description="Interface web para o motor local da ALVESMLD.")
origins = [x.strip() for x in os.getenv("ALVESMLD_CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

# Limite básico em memória por IP; não substitui rate limiting no gateway de produção.
_hits: dict[str, list[float]] = {}
class GenerateRequest(BaseModel):
    description: str = Field(min_length=8, max_length=3000)

@app.middleware("http")
async def simple_rate_limit(request: Request, call_next):
    if request.url.path == "/api/generate" and request.method == "POST":
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        recent = [t for t in _hits.get(ip, []) if now - t < 60]
        if len(recent) >= 5:
            return JSONResponse(status_code=429, content={"detail": "Limite temporário: tente novamente em um minuto."})
        recent.append(now); _hits[ip] = recent
    return await call_next(request)

@app.get("/health")
def health():
    return {"status": "ok", "app": "ALVESMLD", "version": "11.0.0", "engine": "blueprints locais", "executes_generated_tests": False}

@app.post("/api/generate")
def generate(payload: GenerateRequest) -> dict[str, Any]:
    description = payload.description.strip()
    if len(description) < 8:
        raise HTTPException(status_code=422, detail="Descreva o projeto com pelo menos 8 caracteres.")
    project_name = f"{slug(description)[:32]}_{uuid.uuid4().hex[:8]}"
    try:
        project_dir, _, spec, report = gerar_v10(description, project_name, OUT, rodar_testes=False)
        # Gera um ZIP para baixar. O código gerado NÃO é executado pelo servidor web.
        archive_base = OUT / project_name
        archive = Path(shutil.make_archive(str(archive_base), "zip", root_dir=project_dir)).resolve()
        if OUT not in archive.parents:
            raise RuntimeError("Caminho de saída inválido.")
        files = sorted(p.relative_to(project_dir).as_posix() for p in project_dir.rglob("*") if p.is_file())
        return {
            "project_id": project_name,
            "name": project_name,
            "blueprint": spec.get("blueprint", "desconhecido"),
            "files": files,
            "file_count": len(files),
            "tests": {"status": "nao_executado", "message": "Por segurança, o servidor web não executa código de projetos gerados."},
            "requirements_pending": report.get("resumo", {}).get("requisitos_pendentes", 0),
            "warning": "A geração usa blueprints locais; um projeto genérico é apenas um scaffold. Revise o código antes de executar.",
            "download_url": f"/api/download/{project_name}"
        }
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Conflito ao criar projeto; tente novamente.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        # Não expõe caminhos/tracebacks internos ao cliente.
        raise HTTPException(status_code=500, detail=f"Não foi possível gerar o projeto ({type(exc).__name__}).")

@app.get("/api/download/{project_id}")
def download(project_id: str):
    if not re.fullmatch(r"[a-z0-9_-]{1,60}", project_id):
        raise HTTPException(status_code=400, detail="Identificador inválido.")
    archive = (OUT / f"{project_id}.zip").resolve()
    if OUT not in archive.parents or not archive.is_file():
        raise HTTPException(status_code=404, detail="Projeto não encontrado ou link expirado.")
    return FileResponse(archive, media_type="application/zip", filename=f"{project_id}.zip")
