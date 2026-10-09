"""Ferramentas de validação estática para código gerado pelo ALVESMLD.

Não executa código. Compilar/parsear sintaxe não prova correção nem segurança.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ResultadoValidacao:
    valido: bool
    sintaxe_valida: bool
    mensagem: str
    linha: Optional[int] = None
    coluna: Optional[int] = None

    def como_dict(self):
        return asdict(self)

def validar_python(codigo: str) -> ResultadoValidacao:
    if not isinstance(codigo, str) or not codigo.strip():
        return ResultadoValidacao(False, False, "O código está vazio.")
    try:
        ast.parse(codigo)
    except SyntaxError as exc:
        return ResultadoValidacao(False, False, exc.msg, exc.lineno, exc.offset)
    return ResultadoValidacao(True, True, "Sintaxe Python válida. Isso não confirma a lógica nem a segurança.")
