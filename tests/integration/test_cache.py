import time

import pytest

from services.data_gateway.cache import FileCache


@pytest.fixture()
def cache(tmp_path):
    return FileCache(tmp_path / "cache", ttl_seconds=2)


def test_cache_miss_returns_none(cache):
    assert cache.get("nonexistent") is None


def test_cache_set_then_get(cache):
    cache.set("key1", {"value": 42})
    assert cache.get("key1") == {"value": 42}


def test_cache_hit_returns_data(cache):
    cache.set("key2", [1, 2, 3])
    result = cache.get("key2")
    assert result == [1, 2, 3]


def test_cache_ttl_expiry(cache):
    cache.set("key3", "hello")
    time.sleep(2.1)
    assert cache.get("key3") is None


def test_cache_invalidate(cache):
    cache.set("key4", "data")
    cache.invalidate("key4")
    assert cache.get("key4") is None


def test_cache_key_with_special_chars(cache):
    cache.set("fmp/AAPL:annual", {"x": 1})
    assert cache.get("fmp/AAPL:annual") == {"x": 1}
