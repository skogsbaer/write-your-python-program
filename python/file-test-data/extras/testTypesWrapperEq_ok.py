class FileSystemEntry:
    def __init__(self, name: str):
        self.__name = name

    def getName(self) -> str:
        return self.__name

    def getContent(self) -> str:
        raise Exception('No content')

class File(FileSystemEntry):
    def __init__(self, name: str, content: str):
        super().__init__(name)
        self.__content = content

    def getContent(self) -> str:
        return self.__content

_list = []

def foo(entry: FileSystemEntry):
    global _list
    if entry in _list:
        print('Already in list')
    else:
        print('Adding to list')
        _list.append(entry)

f = File('notes.txt', 'Notiz')
foo(f)
foo(File('notes.txt', 'Notiz'))
foo(f)
