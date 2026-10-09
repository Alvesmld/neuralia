"""Motor composicional de projetos do ALVESMLD para Linux.

Sem LLM/serviços externos: interpreta sinais do pedido e compõe arquivos a partir
 de capacidades reutilizáveis. Não promete geração irrestrita de código arbitrário.
"""
from pathlib import Path
import ast, json, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "projetos_gerados"

# Capacidades combináveis. O pedido determina quais módulos entram no projeto.
def inferir_plano(descricao: str, linguagem: str = "Python") -> dict:
    t = (descricao or "").lower()
    if any(x in t for x in ("flutter", "dart", "android", "ios", "app mobile", "aplicativo mobile")):
        linguagem = "Flutter"
    elif any(x in t for x in ("site", "html", "css", "javascript", "página web", "pagina web", "landing page")):
        linguagem = "Web"
    elif any(x in t for x in ("api", "flask", "endpoint", "rest")):
        linguagem = "API Python"
    else:
        linguagem = "Python"
    return {
        "linguagem": linguagem,
        "interface": "gui" if any(x in t for x in ("interface", "janela", "tkinter", "gráfico", "grafico", "visual")) else "cli",
        "persistencia": any(x in t for x in ("salvar", "banco", "persist", "memória", "memoria", "sqlite", "json", "cadastro", "tarefas", "estoque", "contatos")),
        "crud": any(x in t for x in ("cadastro", "gerenciar", "gerenciamento", "tarefas", "estoque", "contatos", "crud", "adicionar", "remover", "listar")),
        "testes": any(x in t for x in ("teste", "testes", "unittest", "qualidade")),
        "descricao": descricao.strip(),
    }


def nome_seguro(nome):
    nome = nome.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", nome):
        raise ValueError("Use 1–48 caracteres: letras sem acento, números, hífen ou sublinhado.")
    BASE.mkdir(parents=True, exist_ok=True)
    alvo = (BASE / nome).resolve()
    if BASE.resolve() not in alvo.parents:
        raise ValueError("Nome de projeto inválido.")
    return alvo


def gerar_python(plano):
    persist = plano["persistencia"]
    crud = plano["crud"]
    gui = plano["interface"] == "gui"
    files = {}
    if gui:
        files["main.py"] = '''"""Aplicação GUI criada pelo motor composicional ALVESMLD."""
import tkinter as tk
from tkinter import messagebox
from core import GestorDados

class App:
    def __init__(self, root):
        self.root = root
        root.title("Aplicação ALVESMLD")
        root.geometry("640x480")
        self.dados = GestorDados()
        self.entrada = tk.Entry(root, width=48)
        self.entrada.pack(padx=12, pady=12)
        tk.Button(root, text="Adicionar", command=self.adicionar).pack()
        self.lista = tk.Listbox(root, width=72, height=16)
        self.lista.pack(padx=12, pady=12, fill="both", expand=True)
        self.atualizar()
    def atualizar(self):
        self.lista.delete(0, tk.END)
        for item in self.dados.listar(): self.lista.insert(tk.END, item)
    def adicionar(self):
        texto = self.entrada.get().strip()
        if not texto:
            messagebox.showinfo("ALVESMLD", "Digite um item primeiro."); return
        self.dados.adicionar(texto); self.entrada.delete(0, tk.END); self.atualizar()
if __name__ == "__main__":
    App(tk.Tk()).root.mainloop()
'''
    else:
        files["main.py"] = '''"""Aplicação de terminal criada pelo motor composicional ALVESMLD."""
from core import GestorDados

def main():
    dados = GestorDados()
    while True:
        print("\\n=== Aplicação ALVESMLD ===")
        print("1) Listar  2) Adicionar  3) Remover  0) Sair")
        op = input("> ").strip()
        if op == "1":
            for i, item in enumerate(dados.listar(), 1): print(f"{i}. {item}")
        elif op == "2":
            valor = input("Novo item: ").strip()
            if valor: dados.adicionar(valor)
        elif op == "3":
            try: dados.remover(int(input("Número: ")) - 1)
            except (ValueError, IndexError): print("Número inválido.")
        elif op == "0": break
        else: print("Opção inválida.")
if __name__ == "__main__": main()
'''
    if persist:
        files["core.py"] = '''"""Lógica reutilizável com persistência JSON."""
import json
from pathlib import Path

class GestorDados:
    def __init__(self, arquivo=None):
        self.arquivo = Path(arquivo) if arquivo else Path(__file__).with_name("dados.json")
        self.itens = self._carregar()
    def _carregar(self):
        try:
            valor = json.loads(self.arquivo.read_text(encoding="utf-8"))
            return valor if isinstance(valor, list) else []
        except (OSError, json.JSONDecodeError): return []
    def _salvar(self):
        self.arquivo.write_text(json.dumps(self.itens, ensure_ascii=False, indent=2), encoding="utf-8")
    def listar(self): return list(self.itens)
    def adicionar(self, item): self.itens.append(str(item)); self._salvar()
    def remover(self, indice):
        if indice < 0 or indice >= len(self.itens): raise IndexError("Item inexistente")
        self.itens.pop(indice); self._salvar()
'''
        files["dados.json"] = "[]\n"
    else:
        files["core.py"] = '''"""Lógica reutilizável em memória."""
class GestorDados:
    def __init__(self): self.itens = []
    def listar(self): return list(self.itens)
    def adicionar(self, item): self.itens.append(str(item))
    def remover(self, indice):
        if indice < 0 or indice >= len(self.itens): raise IndexError("Item inexistente")
        self.itens.pop(indice)
'''
    if plano["testes"]:
        files["test_core.py"] = '''import tempfile, unittest
from pathlib import Path
from core import GestorDados

class TestGestorDados(unittest.TestCase):
    def test_adicionar_listar_remover(self):
        with tempfile.TemporaryDirectory() as tmp:
            gestor = GestorDados(Path(tmp) / "dados.json")
            gestor.adicionar("exemplo")
            self.assertEqual(gestor.listar(), ["exemplo"])
            gestor.remover(0)
            self.assertEqual(gestor.listar(), [])

if __name__ == "__main__": unittest.main()
'''
    return files


def gerar_web(plano):
    return {
        "index.html": '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Projeto ALVESMLD</title><link rel="stylesheet" href="style.css"></head><body><main class="app"><p class="eyebrow">GERADO PELO ALVESMLD</p><h1>Meu projeto</h1><p>Uma base editável criada a partir do seu pedido.</p><form id="form"><input id="entrada" placeholder="Digite um item" required><button>Adicionar</button></form><ul id="lista"></ul></main><script src="app.js"></script></body></html>''',
        "style.css": ''':root{font-family:system-ui,sans-serif;color:#f8fafc;background:#0f172a}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center}.app{width:min(92vw,720px);padding:2rem;border:1px solid #334155;border-radius:1.5rem;background:#1e293b;box-shadow:0 24px 80px #0005}.eyebrow{color:#c4b5fd;letter-spacing:.15em;font-size:.75rem}input,button{padding:.8rem;border-radius:.6rem;border:1px solid #64748b}input{width:65%;background:#0f172a;color:white}button{background:#a78bfa;font-weight:700;cursor:pointer}li{padding:.5rem}''',
        "app.js": '''const form=document.querySelector('#form'), entrada=document.querySelector('#entrada'), lista=document.querySelector('#lista');form.addEventListener('submit',e=>{e.preventDefault();const li=document.createElement('li');li.textContent=entrada.value;lista.appendChild(li);entrada.value='';entrada.focus();});'''
    }


def gerar_api():
    return {"app.py": '''from flask import Flask, jsonify, request
app = Flask(__name__)
_itens = []
@app.get("/")
def inicio(): return jsonify({"nome":"API ALVESMLD", "status":"ok", "rotas":["GET /itens", "POST /itens"]})
@app.get("/itens")
def listar(): return jsonify(_itens)
@app.post("/itens")
def adicionar():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    if not nome: return jsonify({"erro":"Informe nome"}), 400
    _itens.append({"id":len(_itens)+1,"nome":nome})
    return jsonify(_itens[-1]), 201
if __name__ == "__main__": app.run(host="127.0.0.1", port=5000, debug=False)
''', "requirements.txt": "flask>=3.0\n"}


def gerar_flutter():
    return {"lib/main.dart": '''import 'package:flutter/material.dart';
void main() => runApp(const AlvesApp());
class AlvesApp extends StatelessWidget { const AlvesApp({super.key}); @override Widget build(BuildContext context) => MaterialApp(title:'Projeto ALVESMLD', theme:ThemeData(colorSchemeSeed:Colors.deepPurple,useMaterial3:true), home:const Inicio()); }
class Inicio extends StatefulWidget { const Inicio({super.key}); @override State<Inicio> createState()=>_InicioState(); }
class _InicioState extends State<Inicio> { final itens=<String>[]; final entrada=TextEditingController(); @override void dispose(){entrada.dispose();super.dispose();} @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Projeto ALVESMLD')),body:Padding(padding:const EdgeInsets.all(16),child:Column(children:[Row(children:[Expanded(child:TextField(controller:entrada,decoration:const InputDecoration(labelText:'Novo item'))),IconButton(onPressed:(){if(entrada.text.trim().isNotEmpty)setState(()=>itens.add(entrada.text.trim()));entrada.clear();},icon:const Icon(Icons.add))]),Expanded(child:ListView.builder(itemCount:itens.length,itemBuilder:(c,i)=>ListTile(title:Text(itens[i])))])))); }
''', "README.md": "# Projeto Flutter ALVESMLD\n\nCom Flutter instalado, execute `flutter create .` para criar os arquivos de plataforma e depois `flutter run`.\n"}


def compor_projeto(alvo: Path, plano: dict):
    if plano["linguagem"] == "Web": arquivos = gerar_web(plano)
    elif plano["linguagem"] == "API Python": arquivos = gerar_api()
    elif plano["linguagem"] == "Flutter": arquivos = gerar_flutter()
    else: arquivos = gerar_python(plano)
    arquivos["README.md"] = f"# {alvo.name}\n\nProjeto composto pelo motor do ALVESMLD.\n\nPedido original: {plano['descricao'] or '(não informado)'}\n\nLinguagem: {plano['linguagem']}\n\n" + ("Execute `python main.py`. Testes: `python -m unittest`.\n" if plano['linguagem']=="Python" else "Consulte os arquivos do projeto para instruções de execução.\n")
    arquivos["PLANO_ALVESMLD.json"] = json.dumps(plano, ensure_ascii=False, indent=2)
    for rel, conteudo in arquivos.items():
        destino = alvo / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(conteudo, encoding="utf-8")
    (alvo / "PEDIDO_DO_USUARIO.txt").write_text(plano["descricao"] or "Sem descrição informada.", encoding="utf-8")
    return list(arquivos)


def render_studio():
    import streamlit as st
    st.markdown("---")
    st.header("🧠 Estúdio de Programação — motor composicional")
    st.caption("Sem Ollama e sem API externa. O motor interpreta o pedido e compõe módulos reutilizáveis. Não é geração irrestrita como um grande modelo de linguagem.")
    c1,c2 = st.columns([1,1.5])
    with c1:
        nome = st.text_input("Nome do projeto", "meu_projeto", key="studio_v4_nome")
        linguagem = st.selectbox("Tecnologia preferida", ["Automática", "Python", "Web", "API Python", "Flutter"], key="studio_v4_lang")
    with c2:
        descricao = st.text_area("O que você quer que sua IA construa?", placeholder="Ex.: crie um sistema de cadastro de contatos com janela visual, salvamento e testes", height=130, key="studio_v4_desc")
    plano = inferir_plano(descricao, linguagem if linguagem != "Automática" else "Python")
    st.write("**Plano detectado**")
    st.json({k:v for k,v in plano.items() if k != "descricao"})
    st.caption("Python permite compor interface de terminal ou Tkinter, lógica de dados, persistência JSON e testes. Web, API e Flutter possuem geradores iniciais próprios.")
    if st.button("🛠️ Planejar e gerar projeto", type="primary", key="studio_v4_create"):
        try:
            alvo = nome_seguro(nome)
            if alvo.exists() and any(alvo.iterdir()):
                st.error(f"A pasta já contém arquivos: {alvo}. Escolha outro nome para não sobrescrever.")
            else:
                plano = inferir_plano(descricao, linguagem if linguagem != "Automática" else "Python")
                arquivos = compor_projeto(alvo, plano)
                st.session_state["studio_v4_current"] = str(alvo)
                st.success(f"Projeto criado com {len(arquivos)} arquivos.")
        except Exception as exc: st.error(f"Falha ao gerar projeto: {exc}")
    atual = st.session_state.get("studio_v4_current", "")
    if atual and Path(atual).is_dir():
        alvo = Path(atual).resolve()
        st.markdown("#### Projeto atual")
        st.code(str(alvo))
        arquivos = sorted(p for p in alvo.rglob("*") if p.is_file())
        st.write("Arquivos:")
        st.code("\n".join(str(p.relative_to(alvo)) for p in arquivos))
        a,b,c = st.columns(3)
        with a:
            if st.button("🧩 Abrir no VS Code", key="studio_v4_open"):
                exe = shutil.which("code") or shutil.which("codium")
                if not exe: st.error("Não encontrei `code` ou `codium`. Teste `code --version` no terminal.")
                else:
                    try: subprocess.Popen([exe, str(alvo)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True); st.success("Pedido enviado ao editor.")
                    except Exception as exc: st.error(str(exc))
        with b:
            if st.button("🧪 Validar Python", key="studio_v4_check"):
                py = list(alvo.rglob("*.py")); resultados=[]
                for f in py:
                    try: ast.parse(f.read_text(encoding="utf-8")); resultados.append(f"{f.relative_to(alvo)}: sintaxe OK")
                    except SyntaxError as exc: resultados.append(f"{f.relative_to(alvo)}: erro linha {exc.lineno}: {exc.msg}")
                st.code("\n".join(resultados) if resultados else "Nenhum arquivo Python para validar.")
        with c:
            if st.button("📂 Abrir pasta no gerenciador", key="studio_v4_folder"):
                exe = shutil.which("xdg-open")
                if exe: subprocess.Popen([exe, str(alvo)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True); st.success("Pasta aberta.")
                else: st.error("O comando xdg-open não está disponível.")
        opcoes = [str(p.relative_to(alvo)) for p in arquivos]
        preview = st.selectbox("Visualizar arquivo", opcoes, key="studio_v4_preview") if opcoes else None
        if preview:
            p = alvo / preview
            try: st.code(p.read_text(encoding="utf-8")[:20000], language={".py":"python", ".html":"html", ".css":"css", ".js":"javascript", ".dart":"dart", ".json":"json"}.get(p.suffix,"text"))
            except Exception as exc: st.warning(str(exc))
        main = alvo / "main.py"
        if main.is_file():
            st.markdown("#### Execução local")
            autorizado = st.checkbox("Revisei o código e autorizo executar main.py", key="studio_v4_authorize")
            if st.button("▶ Executar main.py", key="studio_v4_run"):
                if not autorizado: st.warning("Revise o código e marque a autorização primeiro.")
                else:
                    try:
                        proc = subprocess.run([sys.executable, "-I", str(main)], cwd=str(alvo), capture_output=True, text=True, timeout=10)
                        st.code((proc.stdout or "") + ("\nSTDERR:\n"+proc.stderr if proc.stderr else "") or "Programa terminou sem saída.")
                        st.write(f"Código de saída: {proc.returncode}")
                    except subprocess.TimeoutExpired: st.error("Execução interrompida após 10 segundos.")
                    except Exception as exc: st.error(str(exc))
    st.warning("Segurança: revise arquivos antes de executar. Esta ferramenta compõe projetos por capacidades; não inventa qualquer algoritmo arbitrário nem modifica arquivos fora da pasta de projetos gerados.")
