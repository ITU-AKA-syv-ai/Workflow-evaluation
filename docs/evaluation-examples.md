# Evaluation Examples

In this guide you will find examples of every kind of evaluation request the system currently supports.

## Rule-based Evaluator

The rule-based evaluator checks LLM outputs against simple, predefined rules. These rules can enforce things like required keywords, allowed formats, or matching patterns. It is mainly used when outputs need to follow strict structure or include/exclude specific content.

### Keyword Rule

Ensure that the output either contains or excludes given keywords.

#### Required

Can be used to ensure critical terms are included in responses. For example, a support response must mention “password” when handling reset instructions.

``` json
[
  {
    "model_output": "To reset your password, click the link sent to your email address.",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1,
        "threshold": 1.0,
        "config": {
          "rules": [
            {
              "name": "keyword",
              "kind": "required",
              "keyword": "password",
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]
```

#### Forbidden

Can be used to prevent unsafe, disallowed, or sensitive content. For example, ensure a response does not contain offensive or restricted words.

``` json
[
  {
    "model_output": "We are unable to process your request at this time.",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1,
        "threshold": 1.0,
        "config": {
          "rules": [
            {
              "name": "keyword",
              "kind": "forbidden",
              "keyword": "damn",
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]
```

### Regex Rule

Can be used to enforce strict output formats like IDs, dates, or codes. For example, validate that an invoice ID follows a required pattern.

``` json
[
  {
    "model_output": "INV-2026-00421",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1,
        "threshold": 1.0,
        "config": {
          "rules": [
            {
              "name": "regex",
              "kind": "required",
              "pattern": "^INV-\\d{4}-\\d{5}$",
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]
```

### Formatting Rule

Ensure that the output is formatted correctly.

#### Valid Json

Can be used to ensure LLM output is valid JSON before parsing or storing. For example, ensure  some user data is structured.

``` json
[
  {
    "model_output": "{\"name\": \"Alice\", \"age\": 29, \"email\": \"alice@example.com\"}",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1,
        "threshold": 1.0,
        "config": {
          "rules": [
            {
              "name": "format",
              "kind": "valid_json",
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]
```

#### Max Length

Can be used to ensure responses fit UI or channel limits (e.g. SMS, chat bubbles). For example, a short confirmation message that must not exceed a character limit.

``` json
[
  {
    "model_output": "Your verification code is 482913. It expires in 10 minutes.",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1,
        "threshold": 1.0,
        "config": {
          "rules": [
            {
              "name": "format",
              "kind": "max_length",
              "max_length": 80,
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]
```

### Combined

These rules work well when used together. For example, ensure API-like output is valid JSON, contains success info, and stays concise.

``` json
[
  {
    "model_output": "{\"status\": \"success\", \"message\": \"Order confirmed\"}",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1,
        "threshold": 0.8,
        "config": {
          "rules": [
            {
              "name": "format",
              "kind": "valid_json",
              "weight": 0.5
            },
            {
              "name": "keyword",
              "kind": "required",
              "keyword": "success",
              "weight": 0.3
            },
            {
              "name": "format",
              "kind": "max_length",
              "max_length": 100,
              "weight": 0.2
            }
          ]
        }
      }
    ]
  }
]
```

## LLM-as-judge Evaluator

Use an LLM to assess the quality of AI output based on subjective criteria like clarity, correctness, and completeness.

``` json
[
  {
    "model_output": "To reduce monthly cloud costs, you should start by identifying unused resources such as idle virtual machines and unattached storage volumes. Then, enable auto-scaling to better match usage with demand. You can also switch to reserved instances for workloads with predictable traffic patterns. Finally, set up budget alerts to monitor spending and avoid unexpected charges.",
    "configs": [
      {
        "evaluator_id": "llm_judge",
        "weight": 1,
        "threshold": 0.8,
        "config": {
          "prompt": "How can I reduce cloud infrastructure costs?",
          "rubric": [
            {
              "id": "correctness",
              "description": "is the advice technically correct?"
            },
            {
              "id": "clarity",
              "description": "is the explanation easy to understand?"
            },
            {
              "id": "completeness",
              "description": "does it cover the main cost-saving strategies?"
            },
            {
              "id": "practicality",
              "description": "are the recommendations actionable in real-world systems?"
            }
          ]
        }
      }
    ]
  }
]
```

### Criteria Suggestions

Here is some inspiration for criteria to use with the LLM-as-judge evaluator.

``` json
"rubric": [
  {
    "id": "correctness",
    "description": "is the information factually and technically correct?"
  },
  {
    "id": "clarity",
    "description": "is the explanation easy to understand and well structured?"
  },
  {
    "id": "completeness",
    "description": "does the response cover the key aspects of the question?"
  },
  {
    "id": "relevance",
    "description": "does the response stay focused on the user’s question?"
  },
  {
    "id": "practicality",
    "description": "are the suggestions actionable in a real-world context?"
  },
  {
    "id": "conciseness",
    "description": "is the response free of unnecessary or repetitive information?"
  },
  {
    "id": "coherence",
    "description": "does the response flow logically from one point to the next?"
  },
  {
    "id": "safety",
    "description": "does the response avoid harmful, unsafe, or inappropriate content?"
  },
  {
    "id": "tone",
    "description": "is the tone appropriate for the context and user intent?"
  },
  {
    "id": "actionability",
    "description": "does the response provide clear next steps or guidance where needed?"
  }
]
```

## Cosine Similarity Evaluator

Measure how semantically similar an AI generated output is to a given reference text. Can be effectively used to evaluate paraphrasing and summarization.

``` json
[
  {
    "model_output": "You can reset your password by clicking on 'Forgot password' on the login page and following the email instructions.",
    "configs": [
      {
        "evaluator_id": "cosine_similarity_evaluator",
        "weight": 1,
        "threshold": 0.75,
        "config": {
          "reference": "To reset your password, use the 'Forgot password' option on the login screen and follow the steps sent to your email."
        }
      }
    ]
  }
]
```

## ROUGE Evaluator

Similarly to the Cosine Similarity evaluator, the ROUGE evaluator measures how much overlap there is between an AI generated output and a reference text and can also be used to effectively evaluate summarization and rewriting, where the output should closely match the meaning and key wording of a reference.

### ROUGE-N (n-gram overlap)

Can be used to check how closely a summary matches a reference by comparing shared word sequences. E.g. pairs of words when `n=2`. 

``` json
[
  {
    "model_output": "The central bank raised interest rates to 4.5 percent in response to persistent inflation pressures across the economy.",
    "configs": [
      {
        "evaluator_id": "rouge_evaluator",
        "weight": 1,
        "threshold": 0.55,
        "config": {
          "reference": "The central bank increased interest rates to 4.5% due to ongoing inflation pressure in the economy.",
          "n_grams": 2
        }
      }
    ]
  }
]
``` 


### ROUGE-L (longest sequence match)

Can be used to check whether the AI generated output preserves the overall meaning and word order, even if the wording is slightly different.

``` json
[
  {
    "model_output": "A new study shows that consistent exercise reduces the risk of heart disease by improving cardiovascular health and lowering blood pressure.",
    "configs": [
      {
        "evaluator_id": "rouge_evaluator",
        "weight": 1,
        "threshold": 0.6,
        "config": {
          "reference": "A recent study found that consistent exercise lowers the risk of heart disease by improving heart health and lowering blood pressure."
        }
      }
    ]
  }
]
```