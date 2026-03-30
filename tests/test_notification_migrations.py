from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.sql.elements import TextClause

# noinspection PyProtectedMember
from storage.schema_migrations import (
    _normalize_event_repeat_type_values,
    run_safe_schema_migrations,
)


def test_run_safe_schema_migrations_upgrades_legacy_notifications_table(tmp_path) -> None:
    db_path = Path(tmp_path) / "legacy_notifications.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text(
                """
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    family_id INTEGER NOT NULL,
                    created_by INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    month INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    calendar_type VARCHAR(50) NOT NULL,
                    repeat_type VARCHAR(50) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE notifications (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    type VARCHAR(50),
                    send_at DATETIME NOT NULL,
                    sent BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    FOREIGN KEY(event_id) REFERENCES events (id)
                )
                """
            )
        )
        connection.execute(text("INSERT INTO users (id) VALUES (1)"))
        connection.execute(
            text(
                """
                INSERT INTO events (
                    id, family_id, created_by, title, month, day, calendar_type, repeat_type
                ) VALUES (
                    1, 1, 1, 'Legacy Event', 3, 18, 'gregorian', 'none'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO notifications (
                    id, user_id, event_id, type, send_at, sent, created_at
                ) VALUES (
                    1, 1, 1, 'reminder', '2026-03-18 00:00:00', 1, '2026-03-18 00:00:00'
                )
                """
            )
        )

    run_safe_schema_migrations(engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("notifications")}
    index_names = {index["name"] for index in inspector.get_indexes("notifications")}

    assert "message" in columns
    assert "type" in columns
    assert "is_read" in columns
    assert columns["event_id"]["nullable"] is True
    assert "ix_notifications_user_event_type" in index_names

    with engine.begin() as connection:
        migrated_row = connection.execute(
            text(
                """
                SELECT message, type, is_read
                FROM notifications
                WHERE id = 1
                """
            )
        ).one()
        assert migrated_row.message == "Legacy notification"
        assert migrated_row.type == "reminder"
        assert migrated_row.is_read == 0

        connection.execute(
            text(
                """
                INSERT INTO notifications (
                    user_id, event_id, message, type, is_read, created_at, send_at, sent
                ) VALUES (
                    1, NULL, 'Invite notification', 'invite', 0, '2026-03-18 00:00:00',
                    NULL, 1
                )
                """
            )
        )


def test_repeat_type_migration_normalizes_uppercase_values_on_sqlite(tmp_path) -> None:
    db_path = Path(tmp_path) / "legacy_repeat_types.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    repeat_type VARCHAR(50) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO events (id, repeat_type) VALUES
                (1, 'NONE'),
                (2, 'WEEKLY')
                """
            )
        )

    run_safe_schema_migrations(engine)

    with engine.begin() as connection:
        rows = connection.execute(
            text("SELECT repeat_type FROM events ORDER BY id")
        ).scalars().all()

    assert rows == ["none", "weekly"]


def test_postgres_repeat_type_normalization_uses_lowercase_update() -> None:
    statements: list[str] = []

    class FakeConnection:
        @staticmethod
        def execute(statement: TextClause) -> None:
            statements.append(str(statement))

    class FakeInspector:
        @staticmethod
        def get_columns(_table_name: str) -> list[dict]:
            return [{"name": "repeat_type", "type": object()}]

    # noinspection PyProtectedMember
    _normalize_event_repeat_type_values(
        FakeConnection(),
        FakeInspector(),
        "postgresql",
        {"events"},
    )

    assert statements[-1].strip() == (
        "UPDATE events\n"
        "            SET repeat_type = LOWER(repeat_type)\n"
        "            WHERE repeat_type <> LOWER(repeat_type)"
    )


def test_postgres_repeat_type_migration_converts_enum_column_to_string() -> None:
    statements: list[str] = []

    class FakeConnection:
        @staticmethod
        def execute(statement: TextClause) -> None:
            statements.append(str(statement))

    class ENUM:
        pass

    class FakeInspector:
        @staticmethod
        def get_columns(_table_name: str) -> list[dict]:
            return [{"name": "repeat_type", "type": ENUM()}]

    # noinspection PyProtectedMember
    _normalize_event_repeat_type_values(
        FakeConnection(),
        FakeInspector(),
        "postgresql",
        {"events"},
    )

    assert statements[-1].strip() == (
        "ALTER TABLE events\n"
        "                ALTER COLUMN repeat_type TYPE VARCHAR(50)\n"
        "                USING LOWER(repeat_type::text)"
    )
