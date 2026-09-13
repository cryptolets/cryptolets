# Tests

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