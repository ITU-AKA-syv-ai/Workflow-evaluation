import pytest
import json
from fastapi.testclient import TestClient

from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.rouge_evaluator import RougeEvaluator
from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry
from tests.conftest import MockProvider


def test_evaluate_rule_based_and_llm_judge(client_with_registry: TestClient, registry: EvaluationRegistry, mock_provider: MockProvider) -> None:
    # Arrange
    evaluator = LLMJudgeEvaluator(mock_provider)
    registry.register(evaluator.name, evaluator)
    registry.register(RuleBasedEvaluator().name, RuleBasedEvaluator())

    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": "1",
                    "threshold": "0.4",
                    "config": {
                        "rules": [
                            {
                                "name": "keyword",
                                "kind": "required",
                                "keyword": "World",
                                "weight": "1.0"
                            }
                        ]
                    }
                },
                {
                    "evaluator_id": "llm_judge",
                    "weight": "1",
                    "threshold": "0.5",
                    "config": {
                        "prompt": "How can I eat bananas most efficiently?",
                        "rubric": [
                            "correctness: is the advice factually correct?",
                            "clarity: is the explanation easy to understand?",
                            "politeness: is the tone appropriate and polite?"
                        ]
                    }
                }
            ]
        }
    ]

    # Act
    response = client_with_registry.post("/evaluate", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    result = response.json()

    print(json.dumps(result, indent=2))

