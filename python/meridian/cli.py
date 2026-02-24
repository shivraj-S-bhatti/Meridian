from __future__ import annotations

import argparse
from datetime import datetime, timezone

from meridian.scoring import ipo_dislocation_score


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Meridian IPO dislocation scoring")
    parser.add_argument("company_id")
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).isoformat())
    parser.add_argument("--horizon-days", type=int, default=28)
    args = parser.parse_args()

    card = ipo_dislocation_score(
        company_id=args.company_id,
        as_of_ts=datetime.fromisoformat(args.as_of.replace("Z", "+00:00")),
        horizon_days=args.horizon_days,
    )
    print(card.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
