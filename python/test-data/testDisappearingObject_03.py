# This test comes from a bug reported by a student, 2025-05-8
from __future__ import annotations
import abc

class FileSystemEntry(abc.ABC):
    def __init__(self, name: str):
        self._name = name
    def getName(self) -> str:
        return self._name
    def getContent(self) -> str:
        raise Exception('No content')
    def getChildren(self) -> list[FileSystemEntry]:
        return []
    def findChild(self, name: str) -> FileSystemEntry:
        for c in self.getChildren():
            if c.getName() == name:
                return c
        raise Exception('No child with name ' + name)
    def addChild(self, child: FileSystemEntry) -> None:
        raise Exception('Cannot add child to ' + repr(self))

class Directory(FileSystemEntry):
    def __init__(self, name: str, children: list[FileSystemEntry] = []):
        super().__init__(name)
        self.__children = children
    def getChildren(self) -> list[FileSystemEntry]:
        return self.__children
    def addChild(self, child: FileSystemEntry):
        self.__children.append(child)
    def __repr__(self):
        return 'Directory(' + repr(self.getName()) + ')'

class File:
    def __init__(self, name: str, content: str):
        raise ValueError()
        super().__init__(name)
        self.content = content
    def getContent(self) -> str:
        return self.content

class Link(FileSystemEntry):
    def __init__(self, name: str, linkTarget: FileSystemEntry):
        super().__init__(name)
        self.__linkTarget = linkTarget
    def getChildren(self) -> list[FileSystemEntry]:
        return self.__linkTarget.getChildren()
    def getContent(self) -> str:
        return self.__linkTarget.getContent()
    def addChild(self, child: FileSystemEntry):
        self.__linkTarget.addChild(child)
    def __repr__(self):
        return ('Link(' + repr(self.getName()) + ' -> ' +
                repr(self.__linkTarget) + ')')
    def getLinkTarget(self) -> FileSystemEntry:
        return self.__linkTarget

class CryptoFile:
    def __init__(self, name: str, content: str):
        raise ValueError()
        super().__init__(name)
        self.content = content
    def getContent(self) -> str:
        return 'CRYPTO_' + 'X'*len(self.content)
    def __repr__(self):
        return 'CryptoFile(' + repr(self.getName())

def test_link():
    stefan  = Directory('stefan', [])
    wehr    = Link('wehr', stefan)
    l1 = [x.getName() for x in wehr.getChildren()]
    wehr.addChild(Directory('subdir', []))
    l2 = [x.getName() for x in wehr.getChildren()]
    print(l2)
    print(stefan)

test_link()
