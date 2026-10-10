"""Docstring and type-hint writer: the prompt, and a safety check that the AI changed nothing but docs and hints. No Qt."""
import ast
import re
import textwrap

from .explain import scope_at


def prompt(code, whole=False):
    where = "this file" if whole else "this code"
    return (f"Edit {where}. Do two things: (1) every function, method and class MUST get a one-line docstring in triple "
            "double quotes as its first statement (skip ones that already have one); (2) every parameter and return "
            "value without a type hint gets one (use built-in forms such as list[int], dict[str, int], int | None; "
            "write -> None when nothing is returned). Do NOT change any logic, names, default values, formatting or "
            "comments. Do NOT add `from __future__` or any import. Give the COMPLETE result in one python block, and "
            "nothing else.\n\n```python\n" + code.strip("\n") + "\n```")


class _Strip(ast.NodeTransformer):
    """Remove docstrings and annotations so two versions can be compared by behaviour."""

    def _clean(self, node):
        self.generic_visit(node)
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
        return node

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = visit_Module = _clean

    def visit_arg(self, node):
        node.annotation = None
        return node

    def visit_AnnAssign(self, node):
        if node.value is None:
            return ast.Pass()
        return ast.Assign(targets=[node.target], value=node.value, lineno=node.lineno)


def _shape(code):
    tree = _Strip().visit(ast.parse(code))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
            node.body = [n for n in node.body if not isinstance(n, ast.Pass)] or [ast.Pass()]
    return ast.dump(tree)


def same_behaviour(old, new):
    """True when the two sources differ only in docstrings, annotations and `from __future__` / typing imports."""
    def drop_imports(code):
        keep = [ln for ln in code.split("\n")
                if not re.match(r"\s*(from __future__ import|from typing import|import typing)", ln)]
        return "\n".join(keep)
    try:
        return _shape(drop_imports(textwrap.dedent(old))) == _shape(drop_imports(textwrap.dedent(new)))
    except SyntaxError:
        return False


def region(source, line, selection=None):
    """(first, last, whole): the lines to document. A selection wins; else the function or class at `line`;
    else the whole file."""
    if selection:
        return selection[0], selection[1], False
    first, last = scope_at(source, line)
    if first == last:
        return 1, max(1, len(source.split("\n"))), True
    return first, last, False


def splice(source, first, last, new_code):
    """Replace lines first..last (1-based) with new_code, keeping the original indentation."""
    lines = source.split("\n")
    old = "\n".join(lines[first - 1:last])
    indent = re.match(r"\s*", lines[first - 1]).group(0)
    if first > 1:                                    # a __future__ import is only legal at the top of a file
        new_code = re.sub(r"^\s*from __future__ import .*\n?", "", new_code, flags=re.M)
    body = textwrap.indent(textwrap.dedent(new_code).strip("\n"), indent)
    lines[first - 1:last] = body.split("\n")
    return "\n".join(lines), old
