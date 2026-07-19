"""Hermetic provider chain for tests: seed-only, no network, fully deterministic."""

from __future__ import annotations

from backend.app.cache import CacheManager
from backend.app.core.config import Settings
from backend.app.providers.chain import ProviderChain
from backend.app.providers.seed_provider import SeedDataProvider


def seed_only_chain(settings: Settings) -> ProviderChain:
    return ProviderChain([SeedDataProvider()], CacheManager(settings), settings=settings)
