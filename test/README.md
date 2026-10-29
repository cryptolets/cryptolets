# Tests

Run the independent parameter regressions without Catapult or network access:
```
python -m unittest discover -s test -p 'test_*.py' -v
```
These use the existing Python dependencies. `vectors/jubjub.json` records the
pinned Arkworks definition behind the Jubjub field, coefficients, and generator.

Runs every kernel through the full flow, against `test/sweeps/`, a copy of `sweeps/`. Keep the copy in sync when a sweep changes.

Note: Run from the repo root, in order.

Run every kernel from the start to RTL verification:
```
./test/hls.sh
```

Run every kernel from logic synthesis to power analysis:
```
./test/syn.sh
```
