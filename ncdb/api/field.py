# api/field.py
import logging
import operator
import os
from .expression import Expression
from .evaluators import (
    DerivedAttributeEvaluator, 
    PointwiseOpEvaluator,
    MovingAverageEvaluator,
    MovingStandardDeviationEvaluator
)

logger = logging.getLogger(__name__)

class Field(Expression):
    def __init__(self, evaluator):
        self._evaluator = evaluator

    @property
    def name(self) -> str:
        return self._evaluator.name

    def __repr__(self):
        return f"<Field {self.name}>"

    def at(self, time):
        return self._evaluator.at(time)

    def __getitem__(self, time):
        return self.at(time)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        current_eval = self._evaluator
        if hasattr(current_eval, "_field") and current_eval._field is not None:
            if current_eval._field.has_derived(current_eval._variable_path, name):
                return Field(evaluator=DerivedAttributeEvaluator(target_field=self, derived_name=name))
                
        raise AttributeError(f"Attribute '{name}' not found for field node.")

    @property
    def cycles(self):
        return self._evaluator.cycles

    def list_attributes(self):
        current_eval = self._evaluator
        if not hasattr(current_eval, "_field") or current_eval._field is None:
            return []
        attrs = current_eval._field.list_derived_attributes(current_eval._variable_path)
        return sorted(attrs)

    def __add__(self, other):
        return Field(evaluator=PointwiseOpEvaluator(self, other, operator.add, "+"))

    def __sub__(self, other):
        return Field(evaluator=PointwiseOpEvaluator(self, other, operator.sub, "-"))

    def __mul__(self, other):
        return Field(evaluator=PointwiseOpEvaluator(self, other, operator.mul, "*"))

    def __truediv__(self, other):
        return Field(evaluator=PointwiseOpEvaluator(self, other, operator.truediv, "/"))

    def moving_avg(self):
        return Field(evaluator=MovingAverageEvaluator(self))

    def moving_std_dev(self):
        return Field(evaluator=MovingStandardDeviationEvaluator(self))
