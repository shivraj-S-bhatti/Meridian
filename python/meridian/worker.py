from __future__ import annotations

import os
import signal
import time
from datetime import datetime, timezone

from meridian.config import settings
from meridian.dom_analyzer import DOMAnalyzer
from meridian.storage import Storage

RUN = True


def _stop(_signum, _frame):
    global RUN
    RUN = False


def run_worker() -> None:
    worker_id = os.getenv("MERIDIAN_WORKER_ID", "worker-1")
    interval = float(os.getenv("MERIDIAN_WORKER_INTERVAL", "2.0"))

    storage = Storage(settings.database_url)
    analyzer = DOMAnalyzer()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while RUN:
        storage.queue_heartbeat(worker_id)

        # Placeholder task demonstrates extraction path and fallback behavior.
        html = (
            "<html><body><p>Management guidance remains strong, but supplier shipment delays are rising.</p></body></html>"
        )
        nodes = analyzer.analyze(
            company_id="WORKER-DEMO",
            url="https://example.com/worker/demo",
            html=html,
            captured_at=datetime.now(timezone.utc),
        )
        storage.save_facts("WORKER-DEMO", nodes)
        time.sleep(interval)


if __name__ == "__main__":
    run_worker()
