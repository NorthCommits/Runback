import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class PayloadReference:
    storage_key: str
    content_size_bytes: int


class LocalPayloadStore:
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path

    async def write(self, trace_id: UUID, content: Any) -> PayloadReference:
        serialized_content = json.dumps(
            content,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
        storage_key = f"{trace_id}/{uuid4().hex}.json"
        destination = self._root_path / storage_key
        await asyncio.to_thread(self._write, destination, serialized_content)
        return PayloadReference(storage_key=storage_key, content_size_bytes=len(serialized_content))

    async def read(self, storage_key: str) -> Any:
        source = self._root_path / Path(storage_key)
        return json.loads((await asyncio.to_thread(source.read_bytes)).decode())

    @staticmethod
    def _write(destination: Path, content: bytes) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
