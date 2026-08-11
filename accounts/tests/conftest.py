import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def limpar_cache_axes():
    cache.clear()
    yield
