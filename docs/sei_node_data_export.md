# SEI Node 3426 Data Export Guide

This guide walks through downloading a compiled PDF report and a CSV telemetry export for node `3426` from the SEI API. Replace the sample base URL and token with your production credentials before running the commands.

---

## 1. Configure environment variables

```bash
export SEI_API_BASE="https://sei.example.com"
export SEI_TOKEN="eyJhbGciOi...REPLACE_WITH_REAL_TOKEN"
```

* `SEI_API_BASE` should point at the deployed SEI environment (for example, `https://sei.example.com`).
* `SEI_TOKEN` must be a valid bearer token that authorizes access to node `3426`.

---

## 2. Download the compiled report (PDF)

The compiled report bundles telemetry, motion events, and snapshots for the requested window.

```bash
curl -sS -H "Authorization: Bearer $SEI_TOKEN" \
  "$SEI_API_BASE/api/v1/nodes/3426/reports?from=2025-11-07T10:00:00Z&to=2025-11-07T11:00:00Z&format=pdf&include=telemetry,snapshots,motion" \
  -o node-3426-report.pdf
```

* The `from`/`to` parameters use ISO-8601 timestamps (UTC).
* The `include` list determines which data categories are packed into the PDF.
* The file is saved locally as `node-3426-report.pdf`.

---

## 3. Export raw telemetry (CSV)

```bash
curl -sS -H "Authorization: Bearer $SEI_TOKEN" \
  "$SEI_API_BASE/api/v1/nodes/3426/export.csv?from=2025-11-07T10:00:00Z&to=2025-11-07T11:00:00Z&fields=timestamp,lat,lon,temperature,motion" \
  -o node-3426-telemetry.csv
```

* Adjust the `fields` query parameter to match the telemetry columns you need.
* The output file is saved locally as `node-3426-telemetry.csv`.

---

## 4. Python helper script (optional)

The repository includes `examples/sei_node_export.py`, which downloads the PDF and CSV using the
same environment variables as the shell script. It also supports optional Postgres loading with
parameterized queries (no SQL string concatenation).

```bash
python examples/sei_node_export.py \
  --from 2025-11-07T00:00:00Z \
  --to 2025-11-07T06:00:00Z \
  --postgres-dsn "dbname=mydb user=me password=secret host=localhost"
```

When `--postgres-dsn` is supplied, the script relies on `psycopg2` and performs inserts using
placeholders:

```python
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
    (...,),
)
```

This parameterized approach prevents SQL injection—never build SQL statements by string concatenation when
user input or exported data is involved.

---

## 5. Troubleshooting tips

* **401 Unauthorized** – Verify that `SEI_TOKEN` is not expired and grants access to node `3426`.
* **404 Not Found** – Confirm the node ID is correct and available in the target environment.
* **Timeouts** – Re-run the command with `-v` to inspect network activity and check connectivity to `SEI_API_BASE`.
* **Partial data** – Narrow the `from`/`to` window and re-run the export to reduce payload size.
