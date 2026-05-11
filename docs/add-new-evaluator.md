### How to add a new evaluator
The application is set up to auto-discover subclasses of the `BaseEvaluator` in the `evaluators` directory.

To add a new evaluator:
1. Ensure the new evaluator class inherits from the `BaseEvaluator` and takes the arguments required by the super class.
2. Add the file containing all logic for the evaluator into the `app/core/evaluators` directory
3. The evaluator is discovered and initialized upon start up of the application.