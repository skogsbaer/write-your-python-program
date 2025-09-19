import ast
import os
import linecache

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


    def getFunDef(self, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        if name in self.__cache:
            return self.__cache[name]
        self.__ensureTree()
        resultNode = None
        if self.__tree:
            for node in ast.walk(self.__tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                    resultNode = node
                    break
        self.__cache[name] = resultNode
        return resultNode

    def getRecordAttr(self, clsName: str, attrName: str) -> ast.AnnAssign | None:
        key = (clsName, attrName)
        if key in self.__cache:
            return self.__cache[key]
        self.__ensureTree()
        # Step 1: find the class
        targetCls = None
        if self.__tree:
            for node in ast.walk(self.__tree):
                if isinstance(node, ast.ClassDef) and node.name == clsName:
                    targetCls = node
                    break
        # Step 2: look for an AnnAssign like:   A: T = ...
        annNode = None
        if targetCls:
            for stmt in targetCls.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if stmt.target.id == attrName:
                        annNode = stmt
        self.__cache[key] = annNode
        return annNode

_cache: dict[str, AST] = {}

def getAST(filename: str) -> AST:
    filename = os.path.normpath(filename)
    if filename not in _cache:
        a = AST(filename)
        _cache[filename] = a
        return a
    else:
        return _cache[filename]
