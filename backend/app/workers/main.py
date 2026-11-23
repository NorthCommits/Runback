import asyncio
import logging

logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info("worker_started")
    await asyncio.Event().wait()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run())


if __name__ == "__main__":
    main()
