### How to add a new evaluator
The application is set up to auto-discover all subclasses of the `BaseEvaluator` class that are found in the `evaluators` directory.

To add a new evaluator:
1. Add/make a file containing the new evaluator in the `app/core/evaluators` directory
2. Ensure the new evaluator class inherits from the `BaseEvaluator` class
   This requires the new evaluator class to implement the abstract methods of the super class as well as a call to the super classes constructor containing the required argument. 
3. The constructor of the new evaluator should at least take two arguments: a `ThresholdConfig` and a `TimeoutConfig`
   From the `registry.py` the evaluator constructor is called with two arguments: a `ThresholdConfig` and a `TimeoutConfig`
   These configurations can be changed to contain the threshold and timeout for the new evaluator in the `settings.py` file or simply ignored.
4. Once the above are completed the evaluator is discovered and initialized upon start up of the application.
   The evaluator is now available for requests.