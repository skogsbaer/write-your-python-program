from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/67

@record
class Directory:
    name: str
    subDirectories: list['Directory']


print(Directory("root", [Directory("media", [])]))