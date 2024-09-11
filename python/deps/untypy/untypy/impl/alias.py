from typing import Any, Optional
import typing

from untypy.interfaces import TypeChecker, CreationContext, TypeCheckerFactory

class TypeAliasTypeFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        # TypeAliasType was introduced in python 3.12
        if hasattr(typing, 'TypeAliasType'):
            if isinstance(annotation, typing.TypeAliasType):
                return ctx.find_checker(annotation.__value__)
        return None
