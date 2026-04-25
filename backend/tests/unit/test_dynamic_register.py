from backend.app.utils.dynamic_register import BaseDynamicRegister
from tests.unit.register_test_directory.test_evaluator2 import BaseEvaluator


class DynamicRegisterTester(BaseDynamicRegister):
    MODULE = "backend.tests.unit.register_test_directory"


class TestDynamicRegister:
    found: dict[str, BaseEvaluator]

    def setup_method(self) -> None:
        register = DynamicRegisterTester(BaseEvaluator, exclude_files={"test_evaluator1.py"})
        self.found = register._found_classes

    def test_dynamic_register_finds_valid_subclass(self) -> None:
        assert len(self.found) == 1
        assert "TestEvaluator2" in self.found

    def test_exclude_files(self) -> None:
        assert len(self.found) == 1
        assert "TestEvaluator1" not in self.found
        assert "__init__.py" not in self.found

    def test_ignores_non_subclasses(self) -> None:
        assert "NotASubclass" not in self.found

    def test_no_files_found(self) -> None:
        register = DynamicRegisterTester(BaseEvaluator, exclude_files={"test_evaluator1.py", "test_evaluator2.py"})
        assert register._found_classes == {}
