use std::collections::HashMap;

/// Disjoint-set (union-find) with path compression and union by rank.
///
/// Maps arbitrary u64 hash values to internal indices for flat-array storage.
pub struct UnionFindInner {
    /// Map from external u64 key to internal index.
    key_to_idx: HashMap<u64, usize>,
    /// Map from internal index back to external u64 key.
    idx_to_key: Vec<u64>,
    parent: Vec<usize>,
    rank: Vec<u8>,
    count: usize,
}

impl UnionFindInner {
    pub fn new() -> Self {
        Self {
            key_to_idx: HashMap::new(),
            idx_to_key: Vec::new(),
            parent: Vec::new(),
            rank: Vec::new(),
            count: 0,
        }
    }

    /// Register a new element. No-op if already present.
    pub fn make_set(&mut self, x: u64) {
        if self.key_to_idx.contains_key(&x) {
            return;
        }
        let idx = self.parent.len();
        self.key_to_idx.insert(x, idx);
        self.idx_to_key.push(x);
        self.parent.push(idx);
        self.rank.push(0);
        self.count += 1;
    }

    /// Find the representative of x (with path splitting).
    pub fn find(&mut self, x: u64) -> u64 {
        let idx = self.key_to_idx[&x];
        let root = self.find_idx(idx);
        self.idx_to_key[root]
    }

    fn find_idx(&mut self, mut idx: usize) -> usize {
        while self.parent[idx] != idx {
            // path splitting: point to grandparent
            self.parent[idx] = self.parent[self.parent[idx]];
            idx = self.parent[idx];
        }
        idx
    }

    /// Union the sets containing a and b.
    pub fn union(&mut self, a: u64, b: u64) {
        let ia = self.key_to_idx[&a];
        let ib = self.key_to_idx[&b];
        let mut ra = self.find_idx(ia);
        let mut rb = self.find_idx(ib);
        if ra == rb {
            return;
        }
        if self.rank[ra] < self.rank[rb] {
            std::mem::swap(&mut ra, &mut rb);
        }
        self.parent[rb] = ra;
        if self.rank[ra] == self.rank[rb] {
            self.rank[ra] += 1;
        }
        self.count -= 1;
    }

    pub fn component_count(&self) -> usize {
        self.count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty() {
        let uf = UnionFindInner::new();
        assert_eq!(uf.component_count(), 0);
    }

    #[test]
    fn test_make_set() {
        let mut uf = UnionFindInner::new();
        uf.make_set(10);
        uf.make_set(20);
        uf.make_set(10); // duplicate, no-op
        assert_eq!(uf.component_count(), 2);
    }

    #[test]
    fn test_find_self() {
        let mut uf = UnionFindInner::new();
        uf.make_set(42);
        assert_eq!(uf.find(42), 42);
    }

    #[test]
    fn test_union() {
        let mut uf = UnionFindInner::new();
        uf.make_set(1);
        uf.make_set(2);
        uf.make_set(3);
        assert_eq!(uf.component_count(), 3);

        uf.union(1, 2);
        assert_eq!(uf.component_count(), 2);
        assert_eq!(uf.find(1), uf.find(2));

        uf.union(2, 3);
        assert_eq!(uf.component_count(), 1);
        assert_eq!(uf.find(1), uf.find(3));
    }

    #[test]
    fn test_union_idempotent() {
        let mut uf = UnionFindInner::new();
        uf.make_set(1);
        uf.make_set(2);
        uf.union(1, 2);
        uf.union(1, 2); // no-op
        assert_eq!(uf.component_count(), 1);
    }
}
