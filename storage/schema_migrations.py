import logging
from typing import Any, cast

from sqlalchemy import Engine, inspect, text

logger = logging.getLogger(__name__)


def run_safe_schema_migrations(engine: Engine) -> None:
    """Run lightweight in-app schema migrations for environments without Alembic."""
    dialect_name = engine.dialect.name

    with engine.begin() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        _normalize_event_repeat_type_values(
            connection,
            inspector,
            dialect_name,
            table_names,
        )

        if "notifications" not in table_names:
            logger.info(
                "Notification schema migration skipped: table missing",
                extra={"migration": "notifications", "dialect": dialect_name},
            )
            return

        reflected_columns = cast(
            list[dict[str, Any]], inspector.get_columns("notifications")
        )
        columns = {column["name"]: column for column in reflected_columns}
        index_names = {
            index["name"] for index in inspector.get_indexes("notifications")
        }
        required_columns = {"message", "type", "is_read"}
        missing_columns = required_columns - set(columns)
        event_id_column = columns.get("event_id")
        event_id_nullable = (
            cast(bool, event_id_column.get("nullable", True))
            if event_id_column is not None
            else True
        )
        duplicate_lookup_index_missing = (
            "ix_notifications_user_event_type" not in index_names
        )

        if (
            not missing_columns
            and event_id_nullable
            and not duplicate_lookup_index_missing
        ):
            logger.info(
                "Notification schema migration not needed",
                extra={"migration": "notifications", "dialect": dialect_name},
            )
            return

        logger.info(
            "Running notification schema migration",
            extra={
                "migration": "notifications",
                "dialect": dialect_name,
                "missing_columns": sorted(missing_columns),
                "event_id_nullable": event_id_nullable,
                "duplicate_lookup_index_missing": duplicate_lookup_index_missing,
            },
        )

        if dialect_name == "sqlite":
            _migrate_notifications_sqlite(connection)
        else:
            _migrate_notifications_generic(connection, missing_columns, event_id_nullable)

        if duplicate_lookup_index_missing:
            _create_notification_duplicate_lookup_index(connection, dialect_name)

        logger.info(
            "Notification schema migration completed",
            extra={"migration": "notifications", "dialect": dialect_name},
        )


def _normalize_event_repeat_type_values(
    connection, inspector, dialect_name: str, table_names: set[str]
) -> None:
    if "events" not in table_names:
        return

    columns = {
        column["name"]: column for column in inspector.get_columns("events")
    }
    if "repeat_type" not in columns:
        return

    repeat_type_column = columns["repeat_type"]

    repeat_type_class_name = repeat_type_column["type"].__class__.__name__.lower()
    if dialect_name == "postgresql" and repeat_type_class_name == "enum":
        connection.execute(
            text(
                """
                ALTER TABLE events
                ALTER COLUMN repeat_type TYPE VARCHAR(50)
                USING LOWER(repeat_type::text)
                """
            )
        )
        return

    connection.execute(
        text(
            """
            UPDATE events
            SET repeat_type = LOWER(repeat_type)
            WHERE repeat_type <> LOWER(repeat_type)
            """
        )
    )


def _migrate_notifications_sqlite(connection) -> None:
    connection.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        connection.execute(text("DROP TABLE IF EXISTS notifications__migration"))
        connection.execute(
            text(
                """
                CREATE TABLE notifications__migration (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NULL,
                    message TEXT NOT NULL DEFAULT 'Legacy notification',
                    type VARCHAR(50) NOT NULL DEFAULT 'system',
                    is_read BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME,
                    send_at DATETIME NULL,
                    sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    FOREIGN KEY(event_id) REFERENCES events (id)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO notifications__migration (
                    id, user_id, event_id, message, type, is_read, created_at, send_at, sent
                )
                SELECT
                    id,
                    user_id,
                    event_id,
                    'Legacy notification',
                    COALESCE(type, 'system'),
                    0,
                    created_at,
                    send_at,
                    COALESCE(sent, 0)
                FROM notifications
                """
            )
        )
        connection.execute(text("DROP TABLE notifications"))
        connection.execute(
            text("ALTER TABLE notifications__migration RENAME TO notifications")
        )
    finally:
        connection.execute(text("PRAGMA foreign_keys=ON"))


def _migrate_notifications_generic(
    connection, missing_columns: set[str], event_id_nullable: bool
) -> None:
    if "message" in missing_columns:
        connection.execute(
            text(
                """
                ALTER TABLE notifications
                ADD COLUMN message TEXT NOT NULL DEFAULT 'Legacy notification'
                """
            )
        )

    if "type" in missing_columns:
        connection.execute(
            text(
                """
                ALTER TABLE notifications
                ADD COLUMN type VARCHAR(50) NOT NULL DEFAULT 'system'
                """
            )
        )

    if "is_read" in missing_columns:
        connection.execute(
            text(
                """
                ALTER TABLE notifications
                ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
        )

    connection.execute(
        text(
            """
            UPDATE notifications
            SET
                message = COALESCE(message, 'Legacy notification'),
                type = COALESCE(type, 'system'),
                is_read = COALESCE(is_read, FALSE)
            """
        )
    )

    if not event_id_nullable:
        connection.execute(
            text("ALTER TABLE notifications ALTER COLUMN event_id DROP NOT NULL")
        )


def _create_notification_duplicate_lookup_index(connection, dialect_name: str) -> None:
    if dialect_name == "sqlite":
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_notifications_user_event_type
                ON notifications (user_id, event_id, type)
                """
            )
        )
        return

    connection.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_notifications_user_event_type
            ON notifications (user_id, event_id, type)
            """
        )
    )
