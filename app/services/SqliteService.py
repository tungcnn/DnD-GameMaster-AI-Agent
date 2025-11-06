from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite


class SqliteService:

    def __init__(self):
        self.conn = None
        self.checkpointer = None

    async def init(self):
        if self.checkpointer:  # ✅ avoid re-init
            return
        self.conn = await aiosqlite.connect("resource/db/checkpoint.db", check_same_thread=False)
        self.checkpointer = AsyncSqliteSaver(self.conn)
        await self.checkpointer.setup()

    async def close(self):
        if self.conn:
            await self.conn.close()


sqlite_service = SqliteService()
