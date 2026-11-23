import asyncio
from pathlib import Path
from uuid import UUID

from app.infrastructure.payloads import LocalPayloadStore


def test_local_payload_store_writes_and_reads_json(tmp_path: Path) -> None:
    store = LocalPayloadStore(tmp_path)
    reference = asyncio.run(
        store.write(UUID("00000000-0000-0000-0000-000000000001"), {"value": 1})
    )

    assert reference.content_size_bytes == len(b'{"value":1}')
    assert asyncio.run(store.read(reference.storage_key)) == {"value": 1}
