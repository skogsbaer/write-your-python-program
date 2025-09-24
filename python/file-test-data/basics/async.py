import asyncio

async def foo(i: int):
    return i + 1

async def main():
    x = await foo("blub")
    print(x)

asyncio.run(main())
