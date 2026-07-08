from datetime import datetime, timedelta
from .field import Field
from .evaluators import BaseEvaluator
from .value import Value

class StaticRangeFilterEvaluator(BaseEvaluator):
    def __init__(self, t1: datetime, t2: datetime, step_hours: int = 6):
        self.t1 = t1
        self.t2 = t2
        self.step_hours = step_hours
        
        # Generate ALL possible thermodynamic cycle coordinates between t1 and t2
        self._cycles = []
        current = t1
        while current <= t2:
            self._cycles.append(current)
            current += timedelta(hours=step_hours)
        
    @property
    def cycles(self):
        return self._cycles

    def at(self, time: datetime) -> Value:
        total_elements = len(self._cycles)
        weight = 1.0 / total_elements if total_elements > 0 else 0.0
        
        if self.t1 <= time <= self.t2:
            return Value(data=weight)
        return Value(data=0.0)


def MovingAverage(t1: datetime, t2: datetime, step_hours: int = 6) -> Field:
    """
    Factory constructing an independent mathematical filter field over all 
    possible nominal cycles in the range.
    """
    evaluator = StaticRangeFilterEvaluator(t1, t2, step_hours)
    return Field(evaluator=evaluator)
