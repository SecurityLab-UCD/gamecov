use std::collections::HashMap;

/// A node in the BK-tree arena.
struct BKNode {
    val: u64,
    children: HashMap<u32, usize>,
}

/// BK-tree for Hamming-distance nearest-neighbour queries on u64 hashes.
///
/// Nodes are stored in a flat Vec (arena allocation) for cache friendliness.
pub struct BKTreeInner {
    nodes: Vec<BKNode>,
}

#[inline(always)]
pub fn hamming(a: u64, b: u64) -> u32 {
    (a ^ b).count_ones()
}

impl BKTreeInner {
    pub fn new() -> Self {
        Self { nodes: Vec::new() }
    }

    /// Insert a hash value. Returns false if exact duplicate (distance 0).
    pub fn add(&mut self, x: u64) -> bool {
        if self.nodes.is_empty() {
            self.nodes.push(BKNode {
                val: x,
                children: HashMap::new(),
            });
            return true;
        }

        let mut idx = 0;
        loop {
            let d = hamming(x, self.nodes[idx].val);
            if d == 0 {
                return false; // exact duplicate
            }
            if let Some(&child_idx) = self.nodes[idx].children.get(&d) {
                idx = child_idx;
            } else {
                let new_idx = self.nodes.len();
                self.nodes.push(BKNode {
                    val: x,
                    children: HashMap::new(),
                });
                self.nodes[idx].children.insert(d, new_idx);
                return true;
            }
        }
    }

    /// Check if any value in the tree is within Hamming distance `radius` of `x`.
    pub fn any_within(&self, x: u64, radius: u32) -> bool {
        if self.nodes.is_empty() {
            return false;
        }

        let mut stack = vec![0usize];
        while let Some(idx) = stack.pop() {
            let node = &self.nodes[idx];
            let d = hamming(x, node.val);
            if d <= radius {
                return true;
            }
            let lo = d.saturating_sub(radius);
            let hi = d + radius;
            for (&dd, &child_idx) in &node.children {
                if dd >= lo && dd <= hi {
                    stack.push(child_idx);
                }
            }
        }
        false
    }

    /// Return all values within Hamming distance `radius` of `x`.
    pub fn find_all_within(&self, x: u64, radius: u32) -> Vec<u64> {
        if self.nodes.is_empty() {
            return Vec::new();
        }

        let mut results = Vec::new();
        let mut stack = vec![0usize];
        while let Some(idx) = stack.pop() {
            let node = &self.nodes[idx];
            let d = hamming(x, node.val);
            if d <= radius {
                results.push(node.val);
            }
            let lo = d.saturating_sub(radius);
            let hi = d + radius;
            for (&dd, &child_idx) in &node.children {
                if dd >= lo && dd <= hi {
                    stack.push(child_idx);
                }
            }
        }
        results
    }

    pub fn len(&self) -> usize {
        self.nodes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_tree() {
        let tree = BKTreeInner::new();
        assert!(tree.is_empty());
        assert!(!tree.any_within(42, 5));
        assert!(tree.find_all_within(42, 5).is_empty());
    }

    #[test]
    fn test_add_and_exact_duplicate() {
        let mut tree = BKTreeInner::new();
        assert!(tree.add(100));
        assert!(!tree.add(100)); // exact duplicate
        assert_eq!(tree.len(), 1);
    }

    #[test]
    fn test_any_within() {
        let mut tree = BKTreeInner::new();
        // 0b0000 and 0b0011 have Hamming distance 2
        tree.add(0b0000);
        assert!(tree.any_within(0b0011, 2));
        assert!(tree.any_within(0b0011, 3));
        assert!(!tree.any_within(0b0011, 1));
    }

    #[test]
    fn test_find_all_within() {
        let mut tree = BKTreeInner::new();
        tree.add(0b0000);
        tree.add(0b0001); // distance 1 from 0b0000
        tree.add(0b0011); // distance 2 from 0b0000
        tree.add(0b0111); // distance 3 from 0b0000
        tree.add(0b1111); // distance 4 from 0b0000

        let results = tree.find_all_within(0b0000, 2);
        assert_eq!(results.len(), 3); // 0b0000, 0b0001, 0b0011
        assert!(results.contains(&0b0000));
        assert!(results.contains(&0b0001));
        assert!(results.contains(&0b0011));
    }

    #[test]
    fn test_hamming_distance() {
        assert_eq!(hamming(0, 0), 0);
        assert_eq!(hamming(0b1111, 0b0000), 4);
        assert_eq!(hamming(0b1010, 0b0101), 4);
        assert_eq!(hamming(0b1100, 0b1010), 2);
        assert_eq!(hamming(u64::MAX, 0), 64);
    }
}
