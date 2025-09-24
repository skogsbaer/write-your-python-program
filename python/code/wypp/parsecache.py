import ast
import os
import linecache
from dataclasses import dataclass
from typing import *

def _firstLineOfFun(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    allLinenos = [node.lineno]
    for e in node.decorator_list:
        allLinenos.append(e.lineno)
    return min(allLinenos)

@dataclass(frozen=True)
class FunMatcher:
    name: str
    firstlineno: Optional[int] = None

    def matches(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        if node.name == self.name:
            if self.firstlineno is not None:
                return self.firstlineno == _firstLineOfFun(node)
            else:
                return True
        else:
            return False

class AST:

    def __init__(self, filename: str):
        """
        Do not instantiate, use getAST
        """
        self.__filename = filename
        self.__tree = None
        self.__treeResolved = False
        self.__cache = {}

    def __ensureTree(self):
        if self.__treeResolved:
            return
        lines = linecache.getlines(self.__filename)
        try:
            tree = ast.parse(''.join(lines))
        except Exception:
            tree = None
        self.__tree = tree
        self.__treeResolved = True

    def _collectFuns(self, nodes: list[ast.stmt], m: FunMatcher, recursive: bool,
                     results: list[ast.FunctionDef | ast.AsyncFunctionDef]):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if m.matches(node):
                    results.append(node)
                if recursive:
                    self._collectFuns(node.body, m, True, results)

    def _findFun(self, nodes: list[ast.stmt], m: FunMatcher, recursive: bool) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        """
        Finds the function from the list of statements that matches m. None is returned
        if no such function is found or if multiple matches are found.
        """
        results = []
        self._collectFuns(nodes, m, recursive, results)
        if len(results) == 1:
            return results[0]
        else:
            return None

    def getFunDef(self, m: FunMatcher) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        if m in self.__cache:
            return self.__cache[m]
        self.__ensureTree()
        if self.__tree:
            resultNode = self._findFun(self.__tree.body, m, True)
        self.__cache[m] = resultNode
        return resultNode

    def _findClass(self, clsName: str) -> ast.ClassDef | None:
        """
        Finds the toplevel class with the given name. Returns None if no such class or
        multiple classes are found.
        """
        targetClss = []
        if self.__tree:
            for node in self.__tree.body:
                if isinstance(node, ast.ClassDef) and node.name == clsName:
                    targetClss.append(node)
        if len(targetClss) == 1:
            return targetClss[0]
        else:
            return None

    def getRecordAttr(self, clsName: str, attrName: str) -> ast.AnnAssign | None:
        """
        Finds the attribute of the format `A: T` or `A: T = ...` with name attrName
        in a toplevel class with name clsName. Returns None if no such class/attribute
        comnbination or mutiples are found.
        """
        key = (clsName, attrName)
        if key in self.__cache:
            return self.__cache[key]
        self.__ensureTree()
        # Step 1: find the class
        targetCls = self._findClass(clsName)
        # Step 2: look for an AnnAssign like:   A: T = ...
        annNodes = []
        if targetCls:
            for stmt in targetCls.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if stmt.target.id == attrName:
                        annNodes.append(stmt)
        annNode = None
        if len(annNodes) == 1:
            annNode = annNodes[0]
        self.__cache[key] = annNode
        return annNode

    def getMethodDef(self, clsName: str, m: FunMatcher) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        """
        Finds the method in class clsName that matches m. None is returned if no such method
        or multiple methods are found.
        """
        key = (clsName, m)
        if key in self.__cache:
            return self.__cache[key]
        self.__ensureTree()
        # Step 1: find the class
        targetCls = self._findClass(clsName)
        # Step 2: look for the method
        funNode = None
        if targetCls:
            funNode = self._findFun(targetCls.body, m, False)
        self.__cache[key] = funNode
        # print(f'clsName={clsName}, m={m}, funNode={funNode}')
        return funNode

_cache: dict[str, AST] = {}

def getAST(filename: str) -> AST:
    filename = os.path.normpath(filename)
    if filename not in _cache:
        a = AST(filename)
        _cache[filename] = a
        return a
    else:
        return _cache[filename]
