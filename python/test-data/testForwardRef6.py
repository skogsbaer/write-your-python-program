from wypp import *
@record
class Directory:
    name: str
    # subDirectories: list[Directory]    # Works but displays a warning in VSCode
    subDirectories2: list['Directory'] # Does not work, but works if the line above is activated!
