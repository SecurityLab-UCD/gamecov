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
├── src/
│   ├── main.py                  # CLI entry point (Typer)
│   └── gamecov/
│       ├── __init__.py          # Public API re-exports
│       ├── cov_base.py          # Abstract protocols: CoverageItem, Coverage, CoverageMonitor
│       ├── frame.py             # Frame dataclass (PIL Image wrapper with average-hash)
│       ├── dedup.py             # Deduplication algorithms (pHash, SSIM [deprecated])
│       ├── frame_cov.py         # FrameCoverage, FrameMonitor, BKFrameMonitor, BK-tree
│       ├── loader.py            # MP4 loading: bulk, lazy (generator), last-n
│       ├── writer.py            # MP4 writing: imageio and OpenCV backends
│       ├── stitch.py            # Panorama stitching of unique frames
│       ├── generator.py         # Hypothesis strategies for property-based testing
│       ├── env.py               # Runtime config (RADIUS env var)
│       └── py.typed             # PEP 561 marker
├── tests/
│   ├── test_generators.py       # Frame/FrameList generation strategies
│   ├── test_dedup.py            # Dedup monotonicity properties
│   ├── test_load_write_random.py# Round-trip write-then-read with random frames
│   ├── test_load_n.py           # load_mp4_last_n correctness
│   ├── test_load_write_assets.py# Differential tests across loaders on real videos
│   ├── test_monotone.py         # Coverage monotonicity (FrameMonitor & BKFrameMonitor)
│   ├── test_BK_frame_monitor.py # Differential: FrameMonitor vs BKFrameMonitor
│   └── test_monotone_smb.py     # Real-world monotonicity on SMB dataset
├── assets/
│   ├── videos/                  # Small sample MP4s for integration tests
│   └── smb/                     # Super Smash Bros recordings for stress tests
├── docs/
│   └── design.md                # Architecture and design documentation
├── pyproject.toml               # Project metadata, dependencies, tool configs
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .github/workflows/           # CI: pytest, mypy, ruff, pylint
├── AGENTS.md                    # This file
└── README.md                    # Human-facing documentation
```

## Design

See [docs/design.md](docs/design.md) for the coverage framework architecture, frame coverage pipeline, BK-tree optimization, and loading strategies.

## Key Modules (quick reference)

| Module | Contents |
|--------|----------|
| `cov_base.py` | `CoverageItem`, `Coverage[T]`, `CoverageMonitor[T]` protocols/ABC |
| `frame.py` | `Frame` dataclass (PIL Image + average-hash) |
| `dedup.py` | `is_dup()`, `dedup_unique_frames()`, `dedup_unique_hashes()`, `ssim_dedup()` [deprecated] |
| `frame_cov.py` | `FrameCoverage`, `FrameMonitor`, `BKFrameMonitor`, `get_frame_cov()` |
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
| `numpy`, `numba` | Numerical arrays, optional JIT acceleration |
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

Some tests require assets in `assets/videos/` or `assets/smb/` and will skip if missing.

### Environment variables for tests

- `RADIUS` — Hamming distance threshold (default `5`).
- `N_MAX` — Maximum number of recordings to process in monotonicity tests (default `100`).

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
- Always run `mypy`, and `ruff` to ensure code quality after updating code in `src/`.
- Never commit changes or create PRs. Suggest commit messages to the human developer for review after your changes to the codebase.
- Always use `typer` to handle CLI commands.

### Scratch Space to Show Your Work and Progress

- Use `.agents/sandbox/` for throwaway exploration that will not be committed.
- Use `.agents/notes/` for longer-term notes that may be useful later. Always write down your plans and reasoning for future reference when encountering major tasks, like adding a feature.
- Use `.agents/accomplished/` for recording completed tasks and the summary of what we did, this may be useful for future reference.
