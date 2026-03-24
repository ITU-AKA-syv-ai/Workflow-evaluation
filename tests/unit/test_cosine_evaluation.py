import random
import string

import pytest

from app.core.evaluators.cosine_evaluator import CosineEvaluator, CosineEvaluatorConfig


class MockEmbeddingClient:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self._embeddings = embeddings

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings


def test_bind_happy_path() -> None:
    standard = "test"
    evaluator = CosineEvaluator(MockEmbeddingClient([]))
    conf = {"standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is not None
    assert bound_conf.standard == standard


def test_bind_error_path() -> None:
    standard = "test"
    evaluator = CosineEvaluator(MockEmbeddingClient([]))
    conf = {"golden_standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is None


def test_bind_edge_case_empty_standard() -> None:
    standard = ""
    evaluator = CosineEvaluator(MockEmbeddingClient([]))
    conf = {"standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is None


def test_bind_edge_case_to_long_standard() -> None:
    length = 2401
    standard = "".join(random.choices(string.ascii_letters, k=length))
    evaluator = CosineEvaluator(MockEmbeddingClient([]))
    conf = {"standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is None


async def test_evaluation_edge_case_empty_input() -> None:
    standard = "test"
    evaluator = CosineEvaluator(MockEmbeddingClient([]))
    conf = CosineEvaluatorConfig(standard=standard)
    result = await evaluator.evaluate("", conf)
    assert result.error is not None


@pytest.mark.asyncio
async def test_evaluation_edge_case_to_long_input() -> None:
    length = 2401
    standard = "test"
    evaluator = CosineEvaluator(MockEmbeddingClient([]))
    conf = CosineEvaluatorConfig(standard=standard)
    output = "".join(random.choices(string.ascii_letters, k=length))
    result = await evaluator.evaluate(output, conf)
    assert result.error is not None


@pytest.mark.asyncio
async def test_evaluation_same_standard_and_input() -> None:
    mock_client = MockEmbeddingClient([
        [1.0, 0.0],
        [1.0, 0.0],
    ])
    standard = "test"
    evaluator = CosineEvaluator(mock_client)
    conf = CosineEvaluatorConfig(standard=standard)
    result = await evaluator.evaluate("test", conf)
    assert result.passed
    assert result.normalised_score == 1


@pytest.mark.asyncio
async def test_evaluation_happy_path_within_threshold() -> None:
    mock_client = MockEmbeddingClient([
        [1.0, 0.0],
        [1.0, 0.5],
    ])
    standard = "Han blev fyret fra sit job"
    evaluator = CosineEvaluator(mock_client)
    conf = CosineEvaluatorConfig(standard=standard)
    result = await evaluator.evaluate("Han mistede sit arbejde", conf)
    assert result.passed


@pytest.mark.asyncio
async def test_evaluation_happy_path_outside_threshold() -> None:
    mock_client = MockEmbeddingClient([
        [1.0, 1.0, 1.0],
        [1.0, 0, 0],
    ])
    standard = "test"
    evaluator = CosineEvaluator(mock_client)
    conf = CosineEvaluatorConfig(standard=standard)
    result = await evaluator.evaluate("kode", conf)
    assert not result.passed


@pytest.mark.asyncio
async def test_evaluation_happy_path_opposite() -> None:
    mock_client = MockEmbeddingClient([
        [1.0, 0.0],
        [0.0, 1.0],
    ])
    standard = "glad"
    evaluator = CosineEvaluator(mock_client)
    conf = CosineEvaluatorConfig(standard=standard)
    result = await evaluator.evaluate("sur", conf)
    assert not result.passed
    assert result.normalised_score == 0
