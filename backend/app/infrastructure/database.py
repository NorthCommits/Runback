import asyncpg


class DatabaseProbe:
    def __init__(self, database_url: str, timeout_seconds: float, ssl_enabled: bool) -> None:
        self._database_url = database_url
        self._timeout_seconds = timeout_seconds
        self._ssl_enabled = ssl_enabled

    async def is_ready(self) -> bool:
        connection: asyncpg.Connection | None = None
        try:
            connection = await asyncpg.connect(
                self._database_url,
                timeout=self._timeout_seconds,
                ssl="require" if self._ssl_enabled else None,
            )
            await connection.execute("SELECT 1")
        except (TimeoutError, OSError, asyncpg.InterfaceError, asyncpg.PostgresError):
            return False
        finally:
            if connection is not None:
                await connection.close()
        return True
