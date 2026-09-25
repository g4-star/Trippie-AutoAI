from sqlalchemy import create_engine, insert, select, text
from sqlalchemy.orm import Session

from app.config import settings, BASE_DIR
from app.models import (
    User,
    Job,
    Application,
    Settings,
    Email,
    EmailReply,
)

SQLITE_PATH = BASE_DIR / "trippie_auto_ai.db"

sqlite_engine = create_engine(
    f"sqlite:///{SQLITE_PATH}"
)

neon_engine = create_engine(
    settings.database_url
)

migration_order = [
    User,
    Job,
    Application,
    Settings,
    Email,
    EmailReply,
]

expected_counts = {
    User: 1,
    Job: 22,
    Application: 2,
    Settings: 1,
    Email: 118,
    EmailReply: 5,
}


def model_name(model):
    return model.__tablename__


print("==================================================")
print("   TrippieAutoAI: SQLite → Neon Migration")
print("==================================================")
print()
print(f"SQLite source : {SQLITE_PATH}")
print("Neon target   : configured DATABASE_URL")
print()

print("=== SOURCE DATA ===")

with Session(sqlite_engine) as source:
    for model in migration_order:
        count = source.scalar(
            select(text("count(*)"))
            .select_from(text(model.__tablename__))
        )
        print(f"{model_name(model):<20} {count}")

print()
print("=== MIGRATION STARTING ===")
print()

with Session(sqlite_engine) as source, Session(neon_engine) as target:
    try:
        # Everything in this target session is committed only once,
        # after every table has been copied successfully.
        for model in migration_order:
            table = model.__table__

            rows = source.execute(
                select(model)
            ).scalars().all()

            print(
                f"Migrating {model_name(model):<20} "
                f"{len(rows):>4} rows..."
            )

            if not rows:
                continue

            records = []

            for row in rows:
                record = {
                    column.name: getattr(row, column.name)
                    for column in table.columns
                }
                records.append(record)

            target.execute(
                insert(model),
                records,
            )

        print()
        print("All records inserted successfully.")
        print("Resetting PostgreSQL sequences...")

        for model in migration_order:
            table_name = model.__tablename__

            sequence_name = target.scalar(
                text(
                    """
                    SELECT pg_get_serial_sequence(
                        :table_name,
                        'id'
                    )
                    """
                ),
                {
                    "table_name": table_name,
                },
            )

            if sequence_name:
                target.execute(
                    text(
                        f"""
                        SELECT setval(
                            '{sequence_name}',
                            COALESCE(
                                (SELECT MAX(id) FROM "{table_name}"),
                                1
                            ),
                            (SELECT COUNT(*) > 0 FROM "{table_name}")
                        )
                        """
                    )
                )

            print(f"Sequence checked: {table_name}")

        target.commit()

    except Exception:
        target.rollback()
        print()
        print("!!! MIGRATION FAILED !!!")
        print("Neon transaction rolled back.")
        print("SQLite was not modified.")
        raise

print()
print("=== VERIFYING NEON ===")

with Session(neon_engine) as target:
    all_ok = True

    for model in migration_order:
        actual = target.scalar(
            select(text("count(*)"))
            .select_from(text(model.__tablename__))
        )

        expected = expected_counts[model]

        status = "OK" if actual == expected else "MISMATCH"

        print(
            f"{model_name(model):<20} "
            f"{actual:>4} / {expected:<4} "
            f"{status}"
        )

        if actual != expected:
            all_ok = False

print()

if not all_ok:
    raise RuntimeError(
        "Migration verification failed: row counts do not match."
    )

print("==================================================")
print("          MIGRATION COMPLETED SUCCESSFULLY")
print("==================================================")
print()
print("SQLite database was left untouched.")
print("All expected Neon row counts match.")
