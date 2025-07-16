from typing import Protocol, Generic, TypeVar, runtime_checkable
from abc import ABC, abstractmethod


@runtime_checkable
class CoverageItem(Protocol):
    """Protocol that all coverage items must implement"""

    def __hash__(self) -> int: ...
    def __str__(self) -> str: ...


T = TypeVar("T", bound=CoverageItem)


class Coverage(ABC, Generic[T]):
    """Abstract base class for coverage types."""

    @property
    @abstractmethod
    def trace(self) -> list[T]:
        """a list of all coverage items in the trace."""

    @property
    @abstractmethod
    def coverage(self) -> set[T]:
        """a set of unique coverage items."""

    @property
    @abstractmethod
    def path_id(self) -> str:
        """unique path ID based on the coverage."""
