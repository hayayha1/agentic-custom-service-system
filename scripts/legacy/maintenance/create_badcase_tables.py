import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import engine
from app.models.base import Base
import app.models # Ensure all models are registered

async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("BadCase tables initialized successfully.")

if __name__ == '__main__':
    asyncio.run(init_tables())
