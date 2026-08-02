# Polaris-Atmospheric-Seeing-
Looking at polars over a peiriod of time, we can calculate atmospheric turbulence, and understand how that affects the errors in images taken during that time.

## CLI

```bash
python calculate.py -constants <path-to-constants-file> -data <path-to-data-directory>
```

The constants file is plain `KEY=value` lines (telescope/site parameters). It can be swapped for different placements; any telescope’s Polaris images should be usable with the matching constants.

## Running tests

From the repo root:

```bash
# Regenerate synthetic FITS fixtures if needed (first time, or after changing the builder)
python3 tests/fixtures/build_mock_data.py

# System tests (full CLI workflow)
python3 -m unittest discover -s tests/system -v
```

More detail: [`tests/README.md`](tests/README.md).
