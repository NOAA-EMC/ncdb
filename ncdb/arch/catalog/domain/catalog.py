from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .variable import Variable
from .obs_space import ObsSpace

from ..orm.base import Base
from ..orm.variable_orm import VariableORM
from ..orm.obs_space_orm import ObsSpaceORM
from ..orm.obs_space_variable_orm import ObsSpaceVariableORM


class Catalog:
    """
    Scientific catalog.

    The Catalog describes scientific concepts and their relationships.
    It does not know about DataStores, DataProducts, or Workflow.
    """

    def __init__(self, database: str = "catalog.db") -> None:
        self.engine = create_engine(
            f"sqlite:///{database}",
            future=True,
        )

        Base.metadata.create_all(self.engine)

    def register(self, asset, context) -> None:
        """Temporary ingestion hook; scientific context handling will be added later."""
        pass

    # ------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------

    def register_variable(
        self,
        name: str,
        description: str | None = None,
    ) -> Variable:

        with Session(self.engine) as session:
            existing = session.scalar(
                select(VariableORM).where(
                    VariableORM.name == name
                )
            )

            if existing is not None:
                return Variable(
                    id=existing.id,
                    name=existing.name,
                    description=existing.description,
                )

            row = VariableORM(
                name=name,
                description=description,
            )

            session.add(row)
            session.commit()
            session.refresh(row)

            return Variable(
                id=row.id,
                name=row.name,
                description=row.description,
            )

    def get_variable(
        self,
        name: str,
    ) -> Variable:

        with Session(self.engine) as session:
            row = session.scalar(
                select(VariableORM).where(
                    VariableORM.name == name
                )
            )

            if row is None:
                raise KeyError(
                    f"Unknown variable: {name}"
                )

            return Variable(
                id=row.id,
                name=row.name,
                description=row.description,
            )

    def list_variables(self) -> list[Variable]:

        with Session(self.engine) as session:
            rows = session.scalars(
                select(VariableORM)
                .order_by(VariableORM.name)
            ).all()

            return [
                Variable(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                )
                for row in rows
            ]

    # ------------------------------------------------------------
    # ObsSpaces
    # ------------------------------------------------------------

    def register_obs_space(
        self,
        name: str,
        description: str | None = None,
    ) -> ObsSpace:

        with Session(self.engine) as session:
            existing = session.scalar(
                select(ObsSpaceORM).where(
                    ObsSpaceORM.name == name
                )
            )

            if existing is not None:
                return ObsSpace(
                    id=existing.id,
                    name=existing.name,
                    description=existing.description,
                )

            row = ObsSpaceORM(
                name=name,
                description=description,
            )

            session.add(row)
            session.commit()
            session.refresh(row)

            return ObsSpace(
                id=row.id,
                name=row.name,
                description=row.description,
            )

    def get_obs_space(
        self,
        name: str,
    ) -> ObsSpace:

        with Session(self.engine) as session:
            row = session.scalar(
                select(ObsSpaceORM).where(
                    ObsSpaceORM.name == name
                )
            )

            if row is None:
                raise KeyError(
                    f"Unknown ObsSpace: {name}"
                )

            return ObsSpace(
                id=row.id,
                name=row.name,
                description=row.description,
            )

    def list_obs_spaces(self) -> list[ObsSpace]:

        with Session(self.engine) as session:
            rows = session.scalars(
                select(ObsSpaceORM)
                .order_by(ObsSpaceORM.name)
            ).all()

            return [
                ObsSpace(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                )
                for row in rows
            ]

    # ------------------------------------------------------------
    # ObsSpace / Variable relationship
    # ------------------------------------------------------------

    def associate(
        self,
        obs_space: ObsSpace,
        variable: Variable,
    ) -> None:

        if obs_space.id is None:
            raise ValueError(
                "ObsSpace has no database ID"
            )

        if variable.id is None:
            raise ValueError(
                "Variable has no database ID"
            )

        with Session(self.engine) as session:
            existing = session.get(
                ObsSpaceVariableORM,
                {
                    "obs_space_id": obs_space.id,
                    "variable_id": variable.id,
                },
            )

            if existing is None:
                session.add(
                    ObsSpaceVariableORM(
                        obs_space_id=obs_space.id,
                        variable_id=variable.id,
                    )
                )
                session.commit()

    def variables(
        self,
        obs_space: ObsSpace,
    ) -> list[Variable]:

        if obs_space.id is None:
            raise ValueError(
                "ObsSpace has no database ID"
            )

        with Session(self.engine) as session:
            rows = session.execute(
                select(VariableORM)
                .join(
                    ObsSpaceVariableORM,
                    VariableORM.id
                    == ObsSpaceVariableORM.variable_id,
                )
                .where(
                    ObsSpaceVariableORM.obs_space_id
                    == obs_space.id
                )
                .order_by(VariableORM.name)
            ).scalars().all()

            return [
                Variable(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                )
                for row in rows
            ]

    def obs_spaces(
        self,
        variable: Variable,
    ) -> list[ObsSpace]:

        if variable.id is None:
            raise ValueError(
                "Variable has no database ID"
            )

        with Session(self.engine) as session:
            rows = session.execute(
                select(ObsSpaceORM)
                .join(
                    ObsSpaceVariableORM,
                    ObsSpaceORM.id
                    == ObsSpaceVariableORM.obs_space_id,
                )
                .where(
                    ObsSpaceVariableORM.variable_id
                    == variable.id
                )
                .order_by(ObsSpaceORM.name)
            ).scalars().all()

            return [
                ObsSpace(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                )
                for row in rows
            ]
