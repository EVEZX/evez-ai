from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass(slots=True)
class RegisteredMutation:
    name: str
    fn: Callable[..., Any]
    safety_bound: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Registry:
    def __init__(self) -> None:
        self._mutations: dict[str, RegisteredMutation] = {}
        self._fitness: dict[str, Callable[..., Any]] = {}
        self._invariants: dict[str, Callable[[Any], bool]] = {}
        self._lock = RLock()

    def register_mutation(self, name: str, fn: Callable[..., Any], *, safety_bound: Any = None, metadata: dict[str, Any] | None = None, overwrite: bool = False) -> None:
        with self._lock:
            if not overwrite and name in self._mutations:
                raise KeyError(f'Mutation already registered: {name}')
            self._mutations[name] = RegisteredMutation(name=name, fn=fn, safety_bound=safety_bound, metadata=metadata or {})

    def register_fitness(self, name: str, fn: Callable[..., Any], *, overwrite: bool = False) -> None:
        with self._lock:
            if not overwrite and name in self._fitness:
                raise KeyError(f'Fitness evaluator already registered: {name}')
            self._fitness[name] = fn

    def register_invariant(self, name: str, fn: Callable[[Any], bool], *, overwrite: bool = False) -> None:
        with self._lock:
            if not overwrite and name in self._invariants:
                raise KeyError(f'Invariant already registered: {name}')
            self._invariants[name] = fn

    def get_mutation(self, name: str) -> RegisteredMutation:
        with self._lock:
            return self._mutations[name]

    def list_mutations(self) -> list[str]:
        with self._lock:
            return sorted(self._mutations)

    def check_invariants(self, state: Any) -> tuple[bool, list[str]]:
        failures: list[str] = []
        with self._lock:
            for name, fn in self._invariants.items():
                try:
                    if not fn(state):
                        failures.append(name)
                except Exception:
                    failures.append(name)
        return (len(failures) == 0, failures)


registry = Registry()
