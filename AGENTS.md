# AGENTS.md - Project Context for Coding Agents

## Project Purpose

`gamecov` defines coverage metrics for video game play-testing, analogous to line/branch coverage in software testing.
A fuzzer drives game sessions, records gameplay as MP4 videos,
and `gamecov` measures how much of the game's visual state space has been explored.
The primary metric today is **frame coverage**:
the number of perceptually unique frames observed across all test sessions.
Future metrics (e.g., audio coverage, state-graph coverage) will follow the same abstract framework.

## Repository Layout

```
.
├── Cargo.toml                   # Rust manifest (maturin builds the extension)
├── pyproject.toml               # Project metadata, maturin build backend
├── src/
│   ├── main.py                  # CLI entry point (Typer)
│   ├── lib.rs                   # PyO3 module entry point (Rust)
│   ├── bktree.rs                # BK-tree<u64> with POPCNT Hamming distance
│   ├── unionfind.rs             # Flat Vec-based union-find
│   ├── monitor.rs               # CoverageTracker (BK-tree + UnionFind combined)
│   └── gamecov/
│       ├── __init__.py          # Public API re-exports
│       ├── _gamecov_core.pyi    # Type stub for Rust extension
│       ├── cov_base.py          # Abstract protocols: CoverageItem, Coverage, CoverageMonitor
│       ├── frame.py             # Frame dataclass (PIL Image wrapper with average-hash)
│       ├── dedup.py             # Deduplication algorithms (pHash, SSIM [deprecated])
│       ├── frame_cov.py         # FrameCoverage, FrameMonitor, BKFrameMonitor, RustBKFrameMonitor, BK-tree, UnionFind
│       ├── loader.py            # MP4 loading: bulk, lazy (generator), last-n
│       ├── writer.py            # MP4 writing: imageio and OpenCV backends
│       ├── stitch.py            # Panorama stitching of unique frames
│       ├── generator.py         # Hypothesis strategies for property-based testing
│       ├── env.py               # Runtime config (RADIUS env var)
│       └── py.typed             # PEP 561 marker
├── rust-tests/
│   └── prop_tests.rs            # Rust proptest property-based tests
├── tests/
│   ├── test_generators.py       # Frame/FrameList generation strategies
│   ├── test_dedup.py            # Dedup monotonicity properties
│   ├── test_load_write_random.py# Round-trip write-then-read with random frames
│   ├── test_load_n.py           # load_mp4_last_n correctness
│   ├── test_load_write_assets.py# Differential tests across loaders on real videos
│   ├── test_monotone.py         # Coverage monotonicity (FrameMonitor & BKFrameMonitor)
│   ├── test_BK_frame_monitor.py # Differential: FrameMonitor vs BKFrameMonitor
│   ├── test_rust_frame_monitor.py # Differential & monotonicity: BKFrameMonitor vs RustBKFrameMonitor
│   └── test_monotone_smb.py     # Real-world monotonicity on SMB dataset
├── benchmarks/
│   ├── conftest.py              # Session-scoped fixtures (pre-generated FrameCoverage)
│   └── test_bench_monitor.py    # Python vs Rust monitor throughput benchmarks
├── assets/
│   ├── videos/                  # Small sample MP4s for integration tests
│   └── smb/                     # Super Smash Bros recordings for stress tests
├── docs/
│   └── design.md                # Architecture and design documentation
├── rustfmt.toml                 # Rust formatting config
├── .pre-commit-config.yaml      # Pre-commit hooks (Python + Rust)
├── .github/workflows/           # CI: pytest, mypy, ruff, pylint, rust (fmt/clippy/test)
├── AGENTS.md                    # This file
└── README.md                    # Human-facing documentation
```

### Rust extension (gamecov-core)

The Rust extension is built as part of the package via maturin. The compiled
module is installed as `gamecov._gamecov_core` and provides high-performance
replacements for the BK-tree, union-find, and coverage tracker.

Build the package (includes Rust compilation): `uv sync` or `pip install .`
Run Rust tests independently: `cargo test`
Check Rust formatting: `cargo fmt --all -- --check`
Run Rust linting: `cargo clippy --all-targets --all-features -- -D warnings`

## Design

See [docs/design.md](docs/design.md) for the coverage framework architecture, frame coverage pipeline, BK-tree optimization, and loading strategies.

## Key Modules (quick reference)

| Module | Contents |
|--------|----------|
| `cov_base.py` | `CoverageItem`, `Coverage[T]`, `CoverageMonitor[T]` protocols/ABC |
| `frame.py` | `Frame` dataclass (PIL Image + average-hash) |
| `dedup.py` | `is_dup()`, `dedup_unique_frames()`, `dedup_unique_hashes()`, `ssim_dedup()` [deprecated] |
| `frame_cov.py` | `FrameCoverage`, `FrameMonitor`, `BKFrameMonitor`, `RustBKFrameMonitor`, `get_frame_cov()`, `_UnionFind`, `_BKTree` |
| `loader.py` | `load_mp4()`, `load_mp4_lazy()`, `load_mp4_last_n()` |
| `writer.py` | `write_mp4()`, `write_mp4_cv2()` |
| `stitch.py` | `stitch_images()` (panorama via AffineStitcher) |
| `generator.py` | Hypothesis strategies: `frames()`, `frames_lists` |
| `env.py` | `RADIUS` env var (Hamming distance threshold, default `5`) |

## Environment and Dependencies

- Python 3.11 managed with `uv` (see `pyproject.toml`).

### Library Usage

| Library | Purpose |
|---------|---------|
| `imageio[ffmpeg]`, `av` | Video decoding/encoding (PyAV plugin) |
| `pillow` | PIL Image representation |
| `imagehash` | Perceptual hashing (pHash, average hash) |
| `opencv-python` | Color conversion, video writing, image processing |
| `scikit-image` | SSIM metric (deprecated path) |
| `stitching` | Panorama stitching via OpenCV features |
| `numpy` | Numerical arrays |
| `gamecov._gamecov_core` | Built-in Rust extension: BK-tree, union-find, coverage tracker (PyO3/maturin) |
| `returns` | Functional `Result` type for error handling |
| `deprecated` | `@deprecated` decorator |
| `typer-slim` | CLI framework |
| `hypothesis` | Property-based testing strategies |

### Dev dependencies

| Library | Purpose |
|---------|---------|
| `mypy` | Static type checking (strict mode, returns plugin) |
| `ruff` | Linting and formatting |
| `pre-commit` | Pre-commit hook runner |
| `pytest-benchmark` | Performance benchmarking (Python vs Rust) |
| `pytest-xdist` | Parallel test execution (`-n auto`) |
| `pytest-cov` | Coverage reporting |
| `pytest-profiling` | Performance profiling |

## Testing

```bash
# Run tests in parallel using all available CPU cores
uv run pytest -n auto
```

### Test categories

- **Property-based** (Hypothesis): `test_generators.py`, `test_dedup.py`, `test_load_write_random.py`
- **Integration** (real assets): `test_load_n.py`, `test_load_write_assets.py`
- **Monotonicity**: `test_monotone.py` (random data), `test_monotone_smb.py` (real SMB recordings)
- **Differential**: `test_BK_frame_monitor.py` (FrameMonitor vs BKFrameMonitor produce identical results)
- **Rust backend**: `test_rust_frame_monitor.py` (differential Python vs Rust, order-independence, monotonicity)

Some tests require assets in `assets/videos/` or `assets/smb/` and will skip if missing.

### Environment variables for tests

- `RADIUS` — Hamming distance threshold (default `5`).
- `N_MAX` — Maximum number of recordings to process in monotonicity tests (default `100`).

## Benchmarks

```bash
# Run benchmarks (disabled by default during normal test runs)
uv run pytest benchmarks/ --benchmark-enable

# Group output by backend for side-by-side comparison
uv run pytest benchmarks/ --benchmark-enable --benchmark-group-by=param:backend

# Save results for later comparison
uv run pytest benchmarks/ --benchmark-enable --benchmark-save=baseline
uv run pytest benchmarks/ --benchmark-enable --benchmark-compare=baseline
```

Benchmarks live in `benchmarks/` and are excluded from the normal test suite.
They compare `BKFrameMonitor` (Python) vs `RustBKFrameMonitor` (Rust) throughput
at the monitor level (`add_cov`/`is_seen` operations).

## Development

- Before start working, refresh your knowledge from contents in `.agents` first.
- Always update README.md and AGENTS.md when you introduce new features or libraries.
- Always write unit tests for integration testing and functional testing of new features.
- Always test your code after your implementation.
- All functions must be fully typed with type hints with input parameters and return types.
  All global constants must also be typed.
  Local variables' types are optional as long as the types can be easily inferred.
- Use f-strings for string interpolation.
- Use `TypedDict`, `Literal`, `Protocol`, and `TypeVar` from `typing` module when appropriate.
- Always run `mypy` and `ruff` to ensure code quality after updating Python code in `src/`.
- Always run `cargo fmt`, `cargo clippy -- -D warnings`, and `cargo test` after updating Rust code in `src/`.
- Never commit changes or create PRs. Suggest commit messages to the human developer for review after your changes to the codebase.
- Always use `typer` to handle CLI commands.

### Scratch Space to Show Your Work and Progress

- Use `.agents/sandbox/` for throwaway exploration that will not be committed.
- Use `.agents/notes/` for longer-term notes that may be useful later. Always write down your plans and reasoning for future reference when encountering major tasks, like adding a feature.
- Use `.agents/accomplished/` for recording completed tasks and the summary of what we did, this may be useful for future reference.
