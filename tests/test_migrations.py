"""Exercise Alembic adoption against isolated databases, never real lead data."""

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[1]
HEAD = "20261003_02"


def config_for(connection):
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


def test_fresh_database_and_history():
    with sa.create_engine("sqlite://").begin() as connection:
        config = config_for(connection)
        command.upgrade(config, "head")
        assert MigrationContext.configure(connection).get_current_revision() == HEAD
        assert [r.revision for r in ScriptDirectory.from_config(config).walk_revisions()] == [HEAD, "20261003_01"]
        columns = {c["name"]: c for c in sa.inspect(connection).get_columns("leads")}
        assert {"budget", "intake", "budget_intake"} <= columns.keys()
        assert all(columns[n]["nullable"] for n in ("budget", "intake"))
        # PostgreSQL metadata parity is checked against PostgreSQL separately;
        # SQLite reflects the portable UUID as CHAR rather than PostgreSQL UUID.


@pytest.mark.parametrize("existing", [(), ("budget",), ("intake",), ("budget", "intake")])
def test_adopts_existing_schema_and_preserves_every_value(existing):
    with sa.create_engine("sqlite://").begin() as connection:
        config = config_for(connection)
        command.upgrade(config, "20261003_01")
        for name in existing:
            connection.execute(sa.text(f"ALTER TABLE leads ADD COLUMN {name} VARCHAR"))
        # Simulate an existing database with no Alembic version history.
        connection.execute(sa.text("DROP TABLE alembic_version"))
        table = sa.Table("leads", sa.MetaData(), autoload_with=connection)
        values = {c.name: "existing value" for c in table.columns if c.name not in ("id", "created_at")}
        values["id"] = "0123456789abcdef0123456789abcdef"
        connection.execute(table.insert().values(**values))
        before = dict(connection.execute(sa.select(table)).mappings().one())
        command.upgrade(config, "head")
        command.upgrade(config, "head")  # No duplicate columns or repeated changes.
        migrated = sa.Table("leads", sa.MetaData(), autoload_with=connection)
        after = dict(connection.execute(sa.select(migrated)).mappings().one())
        assert {k: after[k] for k in before} == before
        assert all(after[n] is None for n in ("budget", "intake") if n not in existing)
        assert MigrationContext.configure(connection).get_current_revision() == HEAD


def test_incompatible_existing_column_fails_without_adding_other_column():
    with sa.create_engine("sqlite://").begin() as connection:
        config = config_for(connection)
        command.upgrade(config, "20261003_01")
        connection.execute(sa.text("ALTER TABLE leads ADD COLUMN budget INTEGER"))
        with pytest.raises(RuntimeError, match="unbounded nullable string"):
            command.upgrade(config, "head")
        assert "intake" not in {c["name"] for c in sa.inspect(connection).get_columns("leads")}
        assert MigrationContext.configure(connection).get_current_revision() == "20261003_01"
