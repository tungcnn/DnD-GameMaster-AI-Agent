from sqlite3 import Connection, connect
from langgraph.checkpoint.sqlite import SqliteSaver


class SqliteService:
    def __init__(self):
        conn: Connection = connect(
            "resource/db/checkpoints.db", check_same_thread=False
        )
        self.checkpointer = SqliteSaver(conn)


sqlite_service = SqliteService()
