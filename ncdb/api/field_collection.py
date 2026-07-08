# api/field_collection.py
import logging
from .expression import Expression

logger = logging.getLogger(__name__)

class FieldCollection(Expression):
    def __init__(self):
        self._fields = []

    def add(self, field):
        self._fields.append(field)

    def fields(self):
        return [repr(f) for f in self._fields]
