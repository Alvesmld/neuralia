"""Treina o Transformer de código do ALVESMLD do zero."""
from __future__ import annotations
import argparse, random, sys
from pathlib import Path
import torch
from torch.nn import functional as F
from codegen.modelo import ModeloCodigo, carregar_corpus, DEFAULT_DATASET, DEFAULT_CHECKPOINT

def criar_blocos(textos, contexto):
    bytes_corpus = b"\n".join(t.encode("utf-8") for t in textos)
    # Janelas contíguas de bytes; alvo é o próximo byte.
    ids = torch.tensor(list(bytes_corpus), dtype=torch.long)
    if len(ids) < contexto + 2:
        raise ValueError(f"Corpus pequeno: {len(ids)} bytes. Adicione exemplos; mínimo sugerido: {contexto+2}.")
    return ids

def avaliar(modelo, ids, contexto, device, lotes=8):
    modelo.eval()
    perdas=[]
    with torch.no_grad():
        for _ in range(lotes):
            if len(ids) <= contexto + 1: break
            ix=torch.randint(0, len(ids)-contexto-1, (min(8, max(1, len(ids)//(contexto+1))),))
            x=torch.stack([ids[i:i+contexto] for i in ix]).to(device)
            y=torch.stack([ids[i+1:i+contexto+1] for i in ix]).to(device)
            perdas.append(F.cross_entropy(modelo(x).reshape(-1,256), y.reshape(-1)).item())
    modelo.train()
    return sum(perdas)/len(perdas) if perdas else float("nan")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default=str(DEFAULT_DATASET))
    ap.add_argument("--saida", default=str(DEFAULT_CHECKPOINT))
    ap.add_argument("--passos", type=int, default=1500)
    ap.add_argument("--contexto", type=int, default=256)
    ap.add_argument("--lote", type=int, default=16)
    ap.add_argument("--d-model", type=int, default=96)
    ap.add_argument("--cabecas", type=int, default=4)
    ap.add_argument("--camadas", type=int, default=3)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--semente", type=int, default=42)
    args=ap.parse_args()
    if args.passos < 1 or args.contexto < 16 or args.lote < 1:
        ap.error("passos/lote devem ser positivos e contexto >= 16")
    random.seed(args.semente); torch.manual_seed(args.semente)
    textos=carregar_corpus(args.dados)
    if not textos:
        raise SystemExit(f"Nenhum exemplo válido em {args.dados}")
    random.shuffle(textos)
    corte=max(1, int(len(textos)*0.9))
    treino=criar_blocos(textos[:corte], args.contexto)
    if len(textos) > 1 and len(textos[corte:]):
        candidato = b"\n".join(t.encode("utf-8") for t in textos[corte:])
        validacao = torch.tensor(list(candidato), dtype=torch.long) if len(candidato) >= args.contexto + 2 else treino
    else:
        validacao = treino
    device="cuda" if torch.cuda.is_available() else "cpu"
    cfg={"d_model":args.d_model,"nhead":args.cabecas,"camadas":args.camadas,"contexto":args.contexto,"dropout":0.1}
    modelo=ModeloCodigo(**cfg).to(device)
    otimizador=torch.optim.AdamW(modelo.parameters(), lr=args.lr, weight_decay=0.01)
    melhor=float("inf")
    destino=Path(args.saida); destino.parent.mkdir(parents=True,exist_ok=True)
    print(f"Exemplos: {len(textos)} | bytes treino: {len(treino)} | dispositivo: {device}")
    print("Treinamento iniciado. A perda não garante código correto; execute avaliações separadas.")
    for passo in range(1,args.passos+1):
        modelo.train()
        ix=torch.randint(0,len(treino)-args.contexto-1,(args.lote,))
        x=torch.stack([treino[i:i+args.contexto] for i in ix]).to(device)
        y=torch.stack([treino[i+1:i+args.contexto+1] for i in ix]).to(device)
        logits=modelo(x); perda=F.cross_entropy(logits.reshape(-1,256),y.reshape(-1))
        otimizador.zero_grad(set_to_none=True); perda.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(),1.0); otimizador.step()
        if passo==1 or passo%100==0 or passo==args.passos:
            val=avaliar(modelo,validacao,args.contexto,device,lotes=4)
            print(f"passo {passo:5d}/{args.passos} | perda treino {perda.item():.4f} | perda validação {val:.4f}")
            if val < melhor:
                melhor=val
                torch.save({"state_dict":modelo.cpu().state_dict(),"config":cfg,"passos":passo,
                            "perda_final":val,"exemplos":len(textos),"nota":"Treinado do zero; modelo experimental."},destino)
                modelo.to(device)
    print(f"Checkpoint salvo em: {destino}")
    print("Próximo passo: python avaliar_codigo.py")

if __name__=="__main__": main()
