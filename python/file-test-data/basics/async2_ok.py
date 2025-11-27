from typing import *
import types
import asyncio
from datetime import datetime

def debug(msg):
    now = datetime.now()
    t = now.strftime('%H:%M:%S.') + f'{int(now.microsecond / 1000):03d}'
    print(f'[{t}] {msg}')

async def meaningOfLife(x: str) -> int:
    debug(f'At start of meaningOfLife: {x}')
    await asyncio.sleep(0.0001)
    debug(f'At end of meaningOfLife: {x}')
    return 42

async def run() -> None:
    a = meaningOfLife('a')
    debug('coroutine object')
    n = await a
    debug(n)

def main():
    asyncio.run(run())

main()
