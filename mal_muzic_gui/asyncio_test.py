import asyncio

async def foo():
    await asyncio.wait([], return_when=asyncio.FIRST_COMPLETED)