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
        _ensure_user_language_column(connection, inspector, dialect_name, table_names)
        _create_notification_delivery_tables(connection, dialect_name, table_names)
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
        required_columns = {"message", "type", "is_read", "metadata"}
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
        if "type" in columns:
            _normalize_legacy_notification_type_values(connection)

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


def _ensure_user_language_column(connection, inspector, dialect_name: str, table_names: set[str]) -> None:
    if "users" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "language" in columns:
        return

    if dialect_name == "sqlite":
        connection.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR(5) NOT NULL DEFAULT 'en'"))
        return

    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) NOT NULL DEFAULT 'en'"))


def _normalize_legacy_notification_type_values(connection) -> None:
    legacy_count = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM notifications
            WHERE type = 'event reminder'
            """
        )
    ).scalar_one()
    if legacy_count:
        logger.warning(
            "Legacy notification type detected",
            extra={
                "migration": "notifications",
                "legacy_type": "event reminder",
                "row_count": legacy_count,
            },
        )
        connection.execute(
            text(
                """
                UPDATE notifications
                SET type = 'EVENT_REMINDER'
                WHERE type = 'event reminder'
                """
            )
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
                    metadata JSON NULL,
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
                    id, user_id, event_id, message, metadata, type, is_read, created_at, send_at, sent
                )
                SELECT
                    id,
                    user_id,
                    event_id,
                    'Legacy notification',
                    NULL,
                    CASE COALESCE(type, 'system')
                        WHEN 'event reminder' THEN 'EVENT_REMINDER'
                        ELSE COALESCE(type, 'system')
                    END,
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

    if "metadata" in missing_columns:
        connection.execute(
            text(
                """
                ALTER TABLE notifications
                ADD COLUMN metadata JSON NULL
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
                type = CASE COALESCE(type, 'system')
                        WHEN 'event reminder' THEN 'EVENT_REMINDER'
                        ELSE COALESCE(type, 'system')
                    END,
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


def _create_notification_delivery_tables(connection, dialect_name: str, table_names: set[str]) -> None:
    if "push_subscriptions" not in table_names:
        if dialect_name == "sqlite":
            connection.execute(text("""
                CREATE TABLE push_subscriptions (
                    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, endpoint TEXT NOT NULL,
                    p256dh_key VARCHAR(512) NOT NULL, auth_key VARCHAR(512) NOT NULL, created_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (id), UNIQUE(user_id, endpoint)
                )
            """))
        else:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), endpoint TEXT NOT NULL,
                    p256dh_key VARCHAR(512) NOT NULL, auth_key VARCHAR(512) NOT NULL, created_at TIMESTAMP,
                    UNIQUE(user_id, endpoint)
                )
            """))
    if "user_notification_preferences" not in table_names:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS user_notification_preferences (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                notify_today BOOLEAN NOT NULL DEFAULT TRUE,
                notify_day_before BOOLEAN NOT NULL DEFAULT TRUE
            )
        """))
