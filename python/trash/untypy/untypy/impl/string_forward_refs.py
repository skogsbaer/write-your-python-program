from typing import Any, Optional

from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext
from untypy.util.typehints import get_type_hints


class StringForwardRefFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is str:
            eval_args = [annotation, globals()]
            local = ctx.eval_context()
            if local is not None:
                eval_args.append(local)

            def resolver(eval_args):
                return eval(*eval_args)

            annotation = get_type_hints(eval_args, ctx, resolver=resolver)
            return ctx.find_checker(annotation)
