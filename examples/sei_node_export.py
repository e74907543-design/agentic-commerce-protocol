#!/usr/bin/env python3
"""Download SEI node exports with optional Postgres loading.

This helper mirrors the shell workflow from ``sei_node_export.sh`` but also
provides a safe path for inserting telemetry rows into Postgres using
parameterized queries via ``psycopg2``.

Usage examples::

    # Save PDF + CSV using defaults
    python examples/sei_node_export.py

    # Custom window and load CSV rows into Postgres
    python examples/sei_node_export.py --from 2025-11-07T00:00:00Z \
        --to 2025-11-07T06:00:00Z \
        --postgres-dsn "dbname=mydb user=me password=secret host=localhost"

Environment variables
---------------------
* ``SEI_API_BASE`` - Required. Base URL for the SEI API (e.g. https://sei.example.com).
* ``SEI_TOKEN`` - Required. Bearer token authorizing access to the node.

"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Iterable

import requests

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    psycopg2 = None  # type: ignore[assignment]


DEFAULT_NODE_ID = "3426"
DEFAULT_FROM = "2025-11-07T10:00:00Z"
DEFAULT_TO = "2025-11-07T11:00:00Z"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Set the {name} environment variable before running this script.")
    return value


def api_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def download_binary(url: str, params: dict[str, str], token: str, dest: Path) -> None:
    response = requests.get(url, headers=api_headers(token), params=params, timeout=30)
    response.raise_for_status()
    dest.write_bytes(response.content)


def download_text(url: str, params: dict[str, str], token: str, dest: Path) -> None:
    response = requests.get(url, headers=api_headers(token), params=params, timeout=30)
    response.raise_for_status()
    dest.write_text(response.text, encoding="utf-8")


def iter_csv_rows(csv_path: Path) -> Iterable[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def load_csv_into_postgres(csv_path: Path, node_id: str, dsn: str) -> None:
    if psycopg2 is None:
        raise SystemExit("psycopg2 is required for Postgres loading. Install it or omit --postgres-dsn.")

    with psycopg2.connect(dsn) as conn:  # type: ignore[call-arg]
        with conn.cursor() as cur:
            for row in iter_csv_rows(csv_path):
                cur.execute(
                    """
                    INSERT INTO sei_node_telemetry
                        (node_id, recorded_at, lat, lon, temperature, motion)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (node_id, recorded_at) DO UPDATE SET
                        lat = EXCLUDED.lat,
                        lon = EXCLUDED.lon,
                        temperature = EXCLUDED.temperature,
                        motion = EXCLUDED.motion
                    """,
                    (
                        node_id,
                        row.get("timestamp"),
                        _maybe_float(row.get("lat")),
                        _maybe_float(row.get("lon")),
                        _maybe_float(row.get("temperature")),
                        _maybe_bool(row.get("motion")),
                    ),
                )


def _maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _maybe_bool(value: str | None) -> bool | None:
    if value in (None, ""):
        return None
    lowered = value.lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return True
    if lowered in {"0", "false", "f", "no", "n"}:
        return False
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node-id", default=DEFAULT_NODE_ID, help="SEI node identifier (default: 3426)")
    parser.add_argument("--from", dest="from_ts", default=DEFAULT_FROM, help="Start of window (ISO-8601 UTC)")
    parser.add_argument("--to", dest="to_ts", default=DEFAULT_TO, help="End of window (ISO-8601 UTC)")
    parser.add_argument(
        "--output-dir",
        default=Path.cwd(),
        type=Path,
        help="Directory where downloads are stored (default: current working directory)",
    )
    parser.add_argument(
        "--postgres-dsn",
        default=None,
        help="Optional psycopg2 connection string used to load the telemetry CSV into Postgres.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    token = require_env("SEI_TOKEN")
    api_base = require_env("SEI_API_BASE")

    report_params = {
        "from": args.from_ts,
        "to": args.to_ts,
        "format": "pdf",
        "include": "telemetry,snapshots,motion",
    }
    report_path = args.output_dir / f"node-{args.node_id}-report.pdf"
    download_binary(f"{api_base}/api/v1/nodes/{args.node_id}/reports", report_params, token, report_path)
    print(f"Saved {report_path}")

    csv_params = {
        "from": args.from_ts,
        "to": args.to_ts,
        "fields": "timestamp,lat,lon,temperature,motion",
    }
    csv_path = args.output_dir / f"node-{args.node_id}-telemetry.csv"
    download_text(f"{api_base}/api/v1/nodes/{args.node_id}/export.csv", csv_params, token, csv_path)
    print(f"Saved {csv_path}")

    if args.postgres_dsn:
        load_csv_into_postgres(csv_path, args.node_id, args.postgres_dsn)
        print("Inserted telemetry rows into Postgres using parameterized queries.")


if __name__ == "__main__":
    main()

