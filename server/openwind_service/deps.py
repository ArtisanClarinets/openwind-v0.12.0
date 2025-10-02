"""FastAPI dependency helpers."""

from __future__ import annotations

from functools import lru_cache

from .openwind_adapter import OpenWInDAdapter
from .optimize import OptimizationManager
from .simulate import SimulationService


@lru_cache
def get_adapter() -> OpenWInDAdapter:
    return OpenWInDAdapter()


@lru_cache
def get_simulation_service() -> SimulationService:
    return SimulationService(get_adapter())


@lru_cache
def get_optimization_manager() -> OptimizationManager:
    return OptimizationManager(get_adapter())


__all__ = ["get_adapter", "get_simulation_service", "get_optimization_manager"]
