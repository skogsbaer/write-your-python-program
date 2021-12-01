from typing import Any, Optional

from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext


class StringForwardRefFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is str:
            eval_args = [annotation, globals()]
            local = ctx.eval_context()
            if local is not None:
                eval_args.append(local)
            annotation = eval(*eval_args)
            return ctx.find_checker(annotation)
