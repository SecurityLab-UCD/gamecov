use pyo3::prelude::*;

pub mod bktree;
pub mod monitor;
pub mod unionfind;

use bktree::BKTreeInner;
use monitor::CoverageTrackerInner;
use unionfind::UnionFindInner;

// ── Python wrappers ───────────────────────────────────────────────────────

/// BK-tree for Hamming-distance queries on 64-bit perceptual hashes.
#[pyclass]
struct BKTree {
    inner: BKTreeInner,
}

#[pymethods]
impl BKTree {
    #[new]
    fn new() -> Self {
        Self {
            inner: BKTreeInner::new(),
        }
    }

    /// Insert a hash. Returns True if new, False if exact duplicate.
    fn add(&mut self, x: u64) -> bool {
        self.inner.add(x)
    }

    /// Check if any stored hash is within Hamming distance `radius` of `x`.
    fn any_within(&self, x: u64, radius: u32) -> bool {
        self.inner.any_within(x, radius)
    }

    /// Return all stored hashes within Hamming distance `radius` of `x`.
    fn find_all_within(&self, x: u64, radius: u32) -> Vec<u64> {
        self.inner.find_all_within(x, radius)
    }

    fn __len__(&self) -> usize {
        self.inner.len()
    }
}

/// Disjoint-set (union-find) over u64 keys.
#[pyclass]
struct UnionFind {
    inner: UnionFindInner,
}

#[pymethods]
impl UnionFind {
    #[new]
    fn new() -> Self {
        Self {
            inner: UnionFindInner::new(),
        }
    }

    fn make_set(&mut self, x: u64) {
        self.inner.make_set(x)
    }

    fn find(&mut self, x: u64) -> u64 {
        self.inner.find(x)
    }

    #[pyo3(name = "union")]
    fn union_sets(&mut self, a: u64, b: u64) {
        self.inner.union(a, b)
    }

    #[getter]
    fn component_count(&self) -> usize {
        self.inner.component_count()
    }
}

/// Combined BK-tree + union-find coverage tracker.
///
/// Drop-in replacement for the hot path of Python's BKFrameMonitor.
#[pyclass]
struct CoverageTracker {
    inner: CoverageTrackerInner,
}

#[pymethods]
impl CoverageTracker {
    #[new]
    fn new(radius: u32) -> Self {
        Self {
            inner: CoverageTrackerInner::new(radius),
        }
    }

    /// Insert a hash. Returns True if the hash was new.
    fn add_hash(&mut self, x: u64) -> bool {
        self.inner.add_hash(x)
    }

    #[getter]
    fn coverage_count(&self) -> usize {
        self.inner.coverage_count()
    }

    #[getter]
    fn total_unique(&self) -> usize {
        self.inner.total_unique()
    }

    fn reset(&mut self) {
        self.inner.reset()
    }
}

/// gamecov_core — Rust-accelerated core for gamecov frame coverage monitoring.
#[pymodule]
#[pyo3(name = "_gamecov_core")]
fn gamecov_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<BKTree>()?;
    m.add_class::<UnionFind>()?;
    m.add_class::<CoverageTracker>()?;
    Ok(())
}
