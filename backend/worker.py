"""
Durable Background Job Worker CLI.

Usage:
    python backend/worker.py [--concurrency 5] [--poll-interval 2.0]
"""
import argparse
import asyncio
from pathlib import Path
import signal
import sys

# Ensure repository root is on sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.database import init_db
from backend.app.services.jobs.worker import JobWorker


async def run_worker(concurrency: int, poll_interval: float, lease_seconds: int, heartbeat_seconds: int):
    logger.info("Initializing Durable Background Job Worker...")
    await init_db()

    worker = JobWorker(
        concurrency=concurrency,
        poll_interval=poll_interval,
        lease_seconds=lease_seconds,
        heartbeat_interval=heartbeat_seconds,
    )

    loop = asyncio.get_running_loop()

    def _signal_handler():
        logger.info("[WorkerCLI] Received termination signal. Initiating graceful shutdown...")
        worker.stop()

    # Register OS signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Signal handling on Windows
            signal.signal(sig, lambda s, f: _signal_handler())

    await worker.start()


def main():
    parser = argparse.ArgumentParser(description="AI Work Layer Durable Job Worker")
    parser.add_argument("--concurrency", type=int, default=settings.JOB_WORKER_CONCURRENCY, help="Max concurrent active jobs")
    parser.add_argument("--poll-interval", type=float, default=settings.JOB_POLL_INTERVAL_SECONDS, help="Polling interval in seconds")
    parser.add_argument("--lease-seconds", type=int, default=settings.JOB_LEASE_SECONDS, help="Worker lease duration in seconds")
    parser.add_argument("--heartbeat-seconds", type=int, default=settings.JOB_HEARTBEAT_SECONDS, help="Heartbeat interval in seconds")

    args = parser.parse_args()

    try:
        asyncio.run(
            run_worker(
                concurrency=args.concurrency,
                poll_interval=args.poll_interval,
                lease_seconds=args.lease_seconds,
                heartbeat_seconds=args.heartbeat_seconds,
            )
        )
    except (KeyboardInterrupt, SystemExit):
        logger.info("[WorkerCLI] Exiting process.")
        sys.exit(0)


if __name__ == "__main__":
    main()
