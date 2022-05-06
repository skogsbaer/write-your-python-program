from wypp import *

def concat_list_left(seq: Sequence[int]) -> list[int]:
    if not isinstance(seq, list):
        raise ValueError(f'{seq!r} is not a list')
    l = seq + [1,2,3]
    return l

def concat_list_right(seq: Sequence[int]) -> list[int]:
    if not isinstance(seq, list):
        raise ValueError(f'{seq!r} is not a list')
    return [1,2,3] + seq

check(concat_list_left([4,5,6]), [4,5,6,1,2,3])
check(concat_list_right([4,5,6]), [1,2,3,4,5,6])

def concat_tuple_left(seq: Sequence[int]) -> tuple[int, ...]:
    return seq + (1,2,3)

def concat_tuple_right(seq: Sequence[int]) -> tuple[int, ...]:
    return (1,2,3) + seq

check(concat_tuple_left((4,5,6)), (4,5,6,1,2,3))
check(concat_tuple_right((4,5,6)), (1,2,3,4,5,6))

def concat_str_left(seq: Sequence) -> str:
    return seq + "123"

def concat_str_right(seq: Sequence) -> str:
    if not isinstance(seq, str):
        raise ValueError("not a string")
    return "123" + seq

check(concat_str_left("456"), "456123")
check(concat_str_right("456"), "123456")
