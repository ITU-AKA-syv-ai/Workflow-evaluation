from app.core.evaluators.rule_based_evaluator import (
    RuleBasedEvaluator, )


def test_bind_happypath() -> None:
    eval = RuleBasedEvaluator()
    conf = {
        "rules": [
            {
                "name": "format",
                "kind": "valid_json",
                "weight": 1.0,
            }
        ]
    }
    bound_conf = eval.validate_config(conf)
    assert bound_conf is not None
    assert len(bound_conf.rules) == 1


def test_bind_errorpath() -> None:
    # invalid top level config. E.g. rules are missing or not a list, wrong/invalid rule in list


def test_evaluation_happypath() -> None:
    # use rules where everything passes

def test_evaluation_edgecase_partial_pass() -> None:
    # one rule fails, another passes

def test_evaluation_edgecase_empty_rules() -> None:
    # empty rulelist, make sure score is 0.0 and reasoning is "no rules were configured"

def test_evaluation_edgecase_weighted_score() -> None:
    # partial success of rules with different weight, make sure aggregated score is correct

def test_evaluation_regex_invalid_is_handled_gracefully() -> None:
    # regex rule invalid. Make sure normal result is returned, reasoning "invalid regex"
