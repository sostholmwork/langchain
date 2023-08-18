"""Test Redis cache functionality."""
import pytest

import langchain
from langchain.cache import RedisCache, RedisSemanticCache
from langchain.schema import Generation, LLMResult
from tests.integration_tests.vectorstores.fake_embeddings import FakeEmbeddings
from tests.unit_tests.llms.fake_chat_model import FakeChatModel
from tests.unit_tests.llms.fake_llm import FakeLLM

REDIS_TEST_URL = "redis://localhost:6379"


def test_redis_cache_ttl() -> None:
    import redis

    langchain.llm_cache = RedisCache(redis_=redis.Redis.from_url(REDIS_TEST_URL), ttl=1)
    langchain.llm_cache.update("foo", "bar", [Generation(text="fizz")])
    key = langchain.llm_cache._key("foo", "bar")
    assert langchain.llm_cache.redis.pttl(key) > 0


def test_redis_cache() -> None:
    import redis

    langchain.llm_cache = RedisCache(redis_=redis.Redis.from_url(REDIS_TEST_URL))
    llm = FakeLLM()
    params = llm.dict()
    params["stop"] = None
    llm_string = str(sorted([(k, v) for k, v in params.items()]))
    langchain.llm_cache.update("foo", llm_string, [Generation(text="fizz")])
    output = llm.generate(["foo"])
    print(output)
    expected_output = LLMResult(
        generations=[[Generation(text="fizz")]],
        llm_output={},
    )
    print(expected_output)
    assert output == expected_output
    langchain.llm_cache.redis.flushall()


def test_redis_cache_chat() -> None:
    import redis

    langchain.llm_cache = RedisCache(redis_=redis.Redis.from_url(REDIS_TEST_URL))
    llm = FakeChatModel()
    params = llm.dict()
    params["stop"] = None
    with pytest.warns():
        llm.predict("foo")
    llm.predict("foo")
    langchain.llm_cache.redis.flushall()


def test_redis_semantic_cache() -> None:
    langchain.llm_cache = RedisSemanticCache(
        embedding=FakeEmbeddings(), redis_url=REDIS_TEST_URL, score_threshold=0.1
    )
    llm = FakeLLM()
    params = llm.dict()
    params["stop"] = None
    llm_string = str(sorted([(k, v) for k, v in params.items()]))
    langchain.llm_cache.update("foo", llm_string, [Generation(text="fizz")])
    output = llm.generate(
        ["bar"]
    )  # foo and bar will have the same embedding produced by FakeEmbeddings
    expected_output = LLMResult(
        generations=[[Generation(text="fizz")]],
        llm_output={},
    )
    assert output == expected_output
    # clear the cache
    langchain.llm_cache.clear(llm_string=llm_string)
    output = llm.generate(
        ["bar"]
    )  # foo and bar will have the same embedding produced by FakeEmbeddings
    # expect different output now without cached result
    assert output != expected_output
    langchain.llm_cache.clear(llm_string=llm_string)


def test_redis_semantic_cache_chat() -> None:
    import redis

    langchain.llm_cache = RedisCache(redis_=redis.Redis.from_url(REDIS_TEST_URL))
    llm = FakeChatModel()
    params = llm.dict()
    params["stop"] = None
    with pytest.warns():
        llm.predict("foo")
    llm.predict("foo")
    langchain.llm_cache.redis.flushall()
