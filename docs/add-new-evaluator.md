### How to add a new evaluator
The application is set up to auto-discover subclasses of the `BaseEvaluator` located in the `evaluators` directory.

To add a new evaluator:
1. Add/make a file containing all logic for the new evaluator into the `app/core/evaluators` directory
2. Ensure the new evaluator class inherits from the `BaseEvaluator`
   This requires the new evaluator class to implement the abstract methods of the super class as well as a call to the super classes constructor containing the required arguments.
3. Once the above are completed the evaluator is discovered and initialized upon start up of the application.
   The evaluator is now available for requests using the `evaluate` endpoint and appears in the list of evaluators provided by the `getEvaluators` endpoint