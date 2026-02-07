use gamecov_core::bktree::{hamming, BKTreeInner};
use gamecov_core::monitor::CoverageTrackerInner;
use gamecov_core::unionfind::UnionFindInner;
use proptest::prelude::*;

// ── BK-tree properties ───────────────────────────────────────────────────

proptest! {
    #[test]
    fn bktree_find_self(x in any::<u64>()) {
        let mut tree = BKTreeInner::new();
        tree.add(x);
        // x should always be within distance 0 of itself
        assert!(tree.any_within(x, 0));
        let results = tree.find_all_within(x, 0);
        assert!(results.contains(&x));
    }

    #[test]
    fn bktree_no_false_negatives(
        values in prop::collection::vec(any::<u64>(), 1..50),
        radius in 0u32..10,
    ) {
        let mut tree = BKTreeInner::new();
        for &v in &values {
            tree.add(v);
        }
        // Every value in the tree must be found by find_all_within on itself
        for &v in &values {
            let results = tree.find_all_within(v, radius);
            assert!(results.contains(&v), "Tree must find the value itself");
        }
    }

    #[test]
    fn bktree_results_within_radius(
        values in prop::collection::vec(any::<u64>(), 1..50),
        query in any::<u64>(),
        radius in 0u32..20,
    ) {
        let mut tree = BKTreeInner::new();
        for &v in &values {
            tree.add(v);
        }
        let results = tree.find_all_within(query, radius);
        // All returned values must actually be within radius
        for &r in &results {
            assert!(
                hamming(query, r) <= radius,
                "Result {} has distance {} from query {}, exceeds radius {}",
                r, hamming(query, r), query, radius
            );
        }
    }

    #[test]
    fn bktree_completeness(
        values in prop::collection::vec(any::<u64>(), 1..30),
        query in any::<u64>(),
        radius in 0u32..10,
    ) {
        let mut tree = BKTreeInner::new();
        for &v in &values {
            tree.add(v);
        }
        let results = tree.find_all_within(query, radius);

        // Brute-force: every value within radius must appear in results
        let mut expected: Vec<u64> = values.iter()
            .copied()
            .filter(|&v| hamming(query, v) <= radius)
            .collect();
        expected.sort();
        expected.dedup();

        let mut got = results.clone();
        got.sort();
        got.dedup();

        assert_eq!(got, expected, "BK-tree must return exactly the brute-force results");
    }
}

// ── UnionFind properties ─────────────────────────────────────────────────

proptest! {
    #[test]
    fn uf_component_count_nonnegative(
        values in prop::collection::vec(any::<u64>(), 0..50),
        unions in prop::collection::vec((any::<prop::sample::Index>(), any::<prop::sample::Index>()), 0..30),
    ) {
        let mut uf = UnionFindInner::new();
        let deduped: Vec<u64> = {
            let mut s = std::collections::HashSet::new();
            values.into_iter().filter(|v| s.insert(*v)).collect()
        };
        for &v in &deduped {
            uf.make_set(v);
        }
        if !deduped.is_empty() {
            for (ia, ib) in &unions {
                let a = deduped[ia.index(deduped.len())];
                let b = deduped[ib.index(deduped.len())];
                uf.union(a, b);
            }
        }
        assert!(uf.component_count() <= deduped.len());
        if !deduped.is_empty() {
            assert!(uf.component_count() >= 1);
        }
    }

    #[test]
    fn uf_union_is_symmetric(a in any::<u64>(), b in any::<u64>()) {
        prop_assume!(a != b);
        let mut uf1 = UnionFindInner::new();
        uf1.make_set(a);
        uf1.make_set(b);
        uf1.union(a, b);

        let mut uf2 = UnionFindInner::new();
        uf2.make_set(a);
        uf2.make_set(b);
        uf2.union(b, a);

        assert_eq!(uf1.find(a), uf1.find(b));
        assert_eq!(uf2.find(a), uf2.find(b));
        assert_eq!(uf1.component_count(), uf2.component_count());
    }
}

// ── CoverageTracker properties ───────────────────────────────────────────

proptest! {
    #[test]
    fn tracker_total_unique_monotone(
        hashes in prop::collection::vec(any::<u64>(), 1..100),
        radius in 1u32..10,
    ) {
        let mut tracker = CoverageTrackerInner::new(radius);
        let mut prev_unique = 0usize;
        for &h in &hashes {
            tracker.add_hash(h);
            assert!(
                tracker.total_unique() >= prev_unique,
                "total_unique must be monotonically non-decreasing"
            );
            prev_unique = tracker.total_unique();
        }
    }

    #[test]
    fn tracker_coverage_leq_unique(
        hashes in prop::collection::vec(any::<u64>(), 1..100),
        radius in 1u32..10,
    ) {
        let mut tracker = CoverageTrackerInner::new(radius);
        for &h in &hashes {
            tracker.add_hash(h);
        }
        assert!(tracker.coverage_count() <= tracker.total_unique());
    }

    #[test]
    fn tracker_reset_clears_state(
        hashes in prop::collection::vec(any::<u64>(), 1..50),
    ) {
        let mut tracker = CoverageTrackerInner::new(5);
        for &h in &hashes {
            tracker.add_hash(h);
        }
        tracker.reset();
        assert_eq!(tracker.coverage_count(), 0);
        assert_eq!(tracker.total_unique(), 0);
    }
}
