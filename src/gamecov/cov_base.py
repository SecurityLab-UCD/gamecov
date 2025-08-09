from typing import Protocol, TypeVar, runtime_checkable


@runtime_checkable
class CoverageItem(Protocol):
    """Protocol that all coverage items must implement"""

    def __hash__(self) -> int: ...
    def __str__(self) -> str: ...


T = TypeVar("T", bound=CoverageItem)


@runtime_checkable
class Coverage(Protocol[T]):
    """Abstract base class for coverage types."""

    @property
    def trace(self) -> list[T]:
        """a list of all coverage items in the trace."""
        ...

    @property
    def coverage(self) -> set[T]:
        """a set of unique coverage items."""
        ...

    @property
    def path_id(self) -> str:
        """unique path ID based on the coverage."""
        ...


@runtime_checkable
class CoverageMonitor(Protocol[T]):
    """Abstract base class for coverage monitors."""

    path_seen: set[str] = set()
    item_seen: set[T] = set()

    def is_seen(self, cov: Coverage[T]) -> bool:
        """Check if the coverage has been seen."""
        ...

    def add_cov(self, cov: Coverage[T]) -> None:
        """Add a new execution coverage record to the monitor."""
        ...

    def reset(self) -> None:
        """Reset the monitor state."""
        self.path_seen.clear()
        self.item_seen.clear()
