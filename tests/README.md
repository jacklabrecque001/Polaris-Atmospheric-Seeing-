# Polaris tests

## Layout

```text
tests/
  fixtures/
    constants/mock_telescope.constants   # KEY=value telescope/site constants
    data/mock_polaris_sequence/          # synthetic FITS cube (regenerable)
    build_mock_data.py                   # rebuilds the cube
  system/
    test_calculate_seeing_monitor.py     # full CLI workflow vs Seeing_monitor.pdf
```

## Run system tests

```bash
cd /home/mike/dev/Polaris-Atmospheric-Seeing-
python3 tests/fixtures/build_mock_data.py   # once, or when regenerating
python3 -m unittest discover -s tests/system -v
```

## Production CLI under test

```bash
python calculate.py -constants <path> -data <path>
```
