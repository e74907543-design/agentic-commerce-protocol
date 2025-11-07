# SEI Node Report and Telemetry Exports

This guide shows how to download compiled reports and raw telemetry exports from the SEI API for a specific node. Replace all placeholder values with your real credentials and desired time ranges before running the commands.

## Prerequisites

1. Obtain the base URL for the SEI deployment (for example, `https://sei.example.com`).
2. Generate an API token that authorizes access to the target node's data.
3. Export the values as environment variables so that subsequent commands can reuse them:

```bash
export SEI_API_BASE="https://sei.example.com"
export SEI_TOKEN="eyJhbGciOi...REPLACE_WITH_REAL_TOKEN"
```

## Download a Compiled PDF Report

The following command fetches a PDF report that includes telemetry, motion events, and snapshots for node `3426` between `2025-11-07T10:00:00Z` and `2025-11-07T11:00:00Z`. Adjust the node ID, time window, and included sections as needed.

```bash
curl -sS \
  -H "Authorization: Bearer $SEI_TOKEN" \
  "$SEI_API_BASE/api/v1/nodes/3426/reports?from=2025-11-07T10:00:00Z&to=2025-11-07T11:00:00Z&format=pdf&include=telemetry,snapshots,motion" \
  -o node-3426-report.pdf
```

## Export Telemetry as CSV

To retrieve raw telemetry for the same period as a CSV file, specify the desired fields through the `fields` query parameter. The example below selects timestamp, latitude, longitude, temperature, and motion columns.

```bash
curl -sS \
  -H "Authorization: Bearer $SEI_TOKEN" \
  "$SEI_API_BASE/api/v1/nodes/3426/export.csv?from=2025-11-07T10:00:00Z&to=2025-11-07T11:00:00Z&fields=timestamp,lat,lon,temperature,motion" \
  -o node-3426-telemetry.csv
```

## Tips

- Use ISO 8601 timestamps (`YYYY-MM-DDTHH:MM:SSZ`) for the `from` and `to` parameters.
- The `include` parameter of the report endpoint accepts a comma-separated list of sections to bundle in the PDF.
- Adjust the `fields` list for the CSV export to match the telemetry columns you need.
- For large time ranges, consider paginating or narrowing the window to avoid large downloads.
