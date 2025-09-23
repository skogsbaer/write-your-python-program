from __future__ import annotations
from wypp import *

class FileSystemEntry:
    def __init__(self, name: str):
        self.__name = name
    def getChildren(self) -> list[FileSystemEntry]:
        return  []
    def addChild(self, entry: FileSystemEntry) -> None:
        raise Exception(f'{self} does not support children')
    def __repr__(self):
        return f'{type(self).__name__}({self.__name})'

class Dir(FileSystemEntry):
    def __init__(self, name: str):
        super().__init__(name)
        self.__children = []
    def getChildren(self) -> list[FileSystemEntry]:
        return self.__children
    def addChild(self, entry: FileSystemEntry):
        self.__children.append(entry)

class File(FileSystemEntry):
    def __init__(self, name: str, content: str):
        super().__init__(name)
        self.__content = content

root = Dir("root")
root.addChild(File("info.txt", "info"))
for x in root.getChildren():
    print(x)
