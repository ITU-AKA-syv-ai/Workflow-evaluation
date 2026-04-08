from fastapi.testclient import TestClient

from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry


def test_evaluate_partial_failure_rule_based_and_llm_judge(
    client_with_registry: TestClient,
    registry: EvaluationRegistry,
    error_provider,
) -> None:
    # Arrange
    failing_evaluator = LLMJudgeEvaluator(error_provider(Exception("Mock provider failure")))
    registry.register(failing_evaluator.name, failing_evaluator)
    registry.register(RuleBasedEvaluator().name, RuleBasedEvaluator())

    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "keyword",
                                "kind": "required",
                                "keyword": "World",
                                "weight": 1.0,
                            }
                        ]
                    },
                },
                {
                    "evaluator_id": "llm_judge",
                    "weight": 1,
                    "threshold": 0.5,
                    "config": {
                        "prompt": "How can I eat bananas most efficiently?",
                        "rubric": [
                            "correctness: is the advice factually correct?",
                            "clarity: is the explanation easy to understand?",
                            "politeness: is the tone appropriate and polite?",
                        ],
                    },
                },
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluate", json=request)

    # Assert
    assert response.status_code == 200
    eval_result = response.json()[0]

    assert eval_result["is_partial"] is True
    assert eval_result["failure_count"] == 1
    assert eval_result["weighted_average_score"] == 1.0

    rule_based_result = eval_result["results"][0]
    llm_judge_result = eval_result["results"][1]

    assert rule_based_result["passed"] is True
    assert rule_based_result["normalised_score"] == 1.0
    assert rule_based_result["error"] is None

    assert llm_judge_result["passed"] is False
    assert llm_judge_result["normalised_score"] == 0
    assert llm_judge_result["error"] is not None