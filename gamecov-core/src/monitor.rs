use std::collections::HashSet;

use crate::bktree::BKTreeInner;
use crate::unionfind::UnionFindInner;

/// Combined BK-tree + UnionFind coverage tracker.
///
/// Mirrors the logic of Python's `BKFrameMonitor.add_cov()`:
/// each new hash is inserted into the BK-tree, all neighbours within
/// `radius` are found, and the hash is unioned with each neighbour.
/// Coverage is measured as the number of connected components.
pub struct CoverageTrackerInner {
    bktree: BKTreeInner,
    uf: UnionFindInner,
    exact: HashSet<u64>,
    radius: u32,
}

impl CoverageTrackerInner {
    pub fn new(radius: u32) -> Self {
        Self {
            bktree: BKTreeInner::new(),
            uf: UnionFindInner::new(),
            exact: HashSet::new(),
            radius,
        }
    }

    /// Insert a hash. Returns true if the hash was new (not an exact duplicate).
    pub fn add_hash(&mut self, x: u64) -> bool {
        if !self.exact.insert(x) {
            return false; // exact duplicate
        }

        let neighbors = self.bktree.find_all_within(x, self.radius);

        self.uf.make_set(x);
        for nb in &neighbors {
            self.uf.union(x, *nb);
        }

        self.bktree.add(x);
        true
    }

    pub fn coverage_count(&self) -> usize {
        self.uf.component_count()
    }

    pub fn total_unique(&self) -> usize {
        self.exact.len()
    }

    pub fn reset(&mut self) {
        self.bktree = BKTreeInner::new();
        self.uf = UnionFindInner::new();
        self.exact.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_tracker() {
        let tracker = CoverageTrackerInner::new(5);
        assert_eq!(tracker.coverage_count(), 0);
        assert_eq!(tracker.total_unique(), 0);
    }

    #[test]
    fn test_single_hash() {
        let mut tracker = CoverageTrackerInner::new(5);
        assert!(tracker.add_hash(42));
        assert_eq!(tracker.coverage_count(), 1);
        assert_eq!(tracker.total_unique(), 1);
    }

    #[test]
    fn test_exact_duplicate() {
        let mut tracker = CoverageTrackerInner::new(5);
        assert!(tracker.add_hash(42));
        assert!(!tracker.add_hash(42)); // duplicate
        assert_eq!(tracker.total_unique(), 1);
        assert_eq!(tracker.coverage_count(), 1);
    }

    #[test]
    fn test_nearby_hashes_merge() {
        let mut tracker = CoverageTrackerInner::new(2);
        // 0b0000 and 0b0001 have Hamming distance 1 (<= radius 2)
        tracker.add_hash(0b0000);
        tracker.add_hash(0b0001);
        assert_eq!(tracker.total_unique(), 2);
        assert_eq!(tracker.coverage_count(), 1); // merged into one component
    }

    #[test]
    fn test_distant_hashes_separate() {
        let mut tracker = CoverageTrackerInner::new(1);
        // 0b0000 and 0b0111 have Hamming distance 3 (> radius 1)
        tracker.add_hash(0b0000);
        tracker.add_hash(0b0111);
        assert_eq!(tracker.total_unique(), 2);
        assert_eq!(tracker.coverage_count(), 2); // separate components
    }

    #[test]
    fn test_bridging_reduces_components() {
        let mut tracker = CoverageTrackerInner::new(1);
        // A: 0b0000, B: 0b0011 (distance 2 from A, separate)
        // C: 0b0001 (distance 1 from A, distance 1 from B -> bridges them)
        tracker.add_hash(0b0000);
        tracker.add_hash(0b0011);
        assert_eq!(tracker.coverage_count(), 2);

        tracker.add_hash(0b0001); // bridges A and B
        assert_eq!(tracker.coverage_count(), 1);
    }

    #[test]
    fn test_reset() {
        let mut tracker = CoverageTrackerInner::new(5);
        tracker.add_hash(1);
        tracker.add_hash(2);
        tracker.reset();
        assert_eq!(tracker.coverage_count(), 0);
        assert_eq!(tracker.total_unique(), 0);
    }
}
