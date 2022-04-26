from wypp import *

class FileSystemEntry:
    def __init__(self, name: str):
        self.__name = name
    def getChildren(self) -> list[FileSystemEntry]:
        return []
    def accept(self, visitor: FileSystemVisitor):
        pass

class Directory(FileSystemEntry):
    def __init__(self, name: str, children: list[FileSystemEntry]):
        super().__init__(name)
        self.__children = children
    def getChildren(self) -> list[FileSystemEntry]:
        return self.__children[:]
    def accept(self, visitor: FileSystemVisitor):
        visitor.visitDirectory(self)

class File(FileSystemEntry):
    def __init__(self, name: str, content: str):
        super().__init__(name)
        self.__content = content
    def getContent(self) -> str:
        return self.__content
    def accept(self, visitor: FileSystemVisitor):
        visitor.visitFile(self)

class FileSystemVisitor:
    def visitDirectory(self, dir: Directory):
        pass
    def visitFile(self, file: File):
        pass

class TotalSizeVisitor(FileSystemVisitor):
    def __init__(self):
        self.__totalSize = 0
    def visitDirectory(self, dir: Directory):
        for c in dir.getChildren():
            c.accept(self)
    def visitFile(self, file: str):
        # Invalid override
        self.__totalSize += len(file)
    def getTotalSize(self):
        return self.__totalSize

def computeTotalSize(fs: FileSystemEntry) -> int:
    visitor = TotalSizeVisitor()
    fs.accept(visitor)
    return visitor.getTotalSize()

stefan = Directory('stefan', [File('notes.txt', 'Notiz')])
claudia = Directory('claudia', [File('regex.py', '#!/usr/bin/python')])
home = Directory('home', [stefan, claudia])
root = Directory('', [File('notes.txt', 'blub'), home])
print(computeTotalSize(root))
