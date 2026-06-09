"""
OdontoAI — Database Initializer
Run this once to create the database and tables.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from database import init_db, DB_PATH


async def main():
    print(f"🦷 Inicializando banco OdontoAI em: {DB_PATH}")
    await init_db()
    print("✅ Banco criado com sucesso!")
    print(f"   📁 {DB_PATH}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
