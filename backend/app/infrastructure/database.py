import asyncpg
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


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


def create_engine(database_url: str, ssl_enabled: bool) -> AsyncEngine:
    return create_async_engine(
        to_async_database_url(database_url),
        connect_args={"ssl": "require"} if ssl_enabled else {},
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def to_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise ValueError("RUNBACK_DATABASE_URL must use the postgresql scheme")
