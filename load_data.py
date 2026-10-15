"""Create the intake schema and load class_dataset.csv into Postgres."""

import csv
import os
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.sql"
CSV_CANDIDATES = (
    ROOT / "data" / "class_dataset.csv",
    ROOT / "class_dataset.csv",
)

TABLES = (
    "school_years",
    "intro_programming",
    "tools",
    "availability_slots",
    "students",
    "student_tools",
    "student_availability",
)


def load_dotenv(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def normalize_netid(raw: str) -> str:
    netid = raw.strip().lower()
    suffix = "@nyu.edu"
    if netid.endswith(suffix):
        netid = netid[: -len(suffix)]
    return netid


def split_values(cell: str) -> list[str]:
    return [part.strip() for part in cell.split(";") if part.strip()]


def csv_path() -> Path:
    for path in CSV_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find class_dataset.csv in data/ or the project root."
    )


def lookup_id(cur, cache: dict[str, int], table: str, id_column: str, value_column: str, value: str) -> int:
    if value not in cache:
        cur.execute(
            f"INSERT INTO {table} ({value_column}) VALUES (%s) RETURNING {id_column}",
            (value,),
        )
        cache[value] = cur.fetchone()[0]
    return cache[value]


def main() -> None:
    load_dotenv(ROOT / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is missing from .env")
    if "railway.internal" in database_url:
        raise SystemExit(
            "DATABASE_URL uses the private Railway host (railway.internal). "
            "Use DATABASE_PUBLIC_URL from the laptop."
        )

    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DROP TABLE IF EXISTS
                        student_availability,
                        student_tools,
                        students,
                        availability_slots,
                        tools,
                        intro_programming,
                        school_years
                    CASCADE
                    """
                )
                cur.execute(SCHEMA_PATH.read_text())

                school_years: dict[str, int] = {}
                backgrounds: dict[str, int] = {}
                tools: dict[str, int] = {}
                slots: dict[str, int] = {}

                with csv_path().open(newline="", encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        school_year_id = lookup_id(
                            cur, school_years, "school_years", "school_year_id", "label", row["school_year"].strip()
                        )
                        intro_id = lookup_id(
                            cur,
                            backgrounds,
                            "intro_programming",
                            "intro_programming_id",
                            "code",
                            row["intro_programming"].strip(),
                        )
                        cur.execute(
                            """
                            INSERT INTO students (
                                netid, name, school_year_id, intro_programming_id,
                                skill_programming, skill_data_stats,
                                skill_frontend_design, skill_business_pitch,
                                working_style, interests, semester_goal, submitted_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING student_id
                            """,
                            (
                                normalize_netid(row["netid"]),
                                row["name"].strip(),
                                school_year_id,
                                intro_id,
                                int(row["skill_programming"]),
                                int(row["skill_data_stats"]),
                                int(row["skill_frontend_design"]),
                                int(row["skill_business_pitch"]),
                                row["working_style"].strip(),
                                row["interests"].strip(),
                                row["semester_goal"].strip(),
                                row["submitted_at"].strip(),
                            ),
                        )
                        student_id = cur.fetchone()[0]

                        for tool in split_values(row["tools"]):
                            tool_id = lookup_id(cur, tools, "tools", "tool_id", "name", tool)
                            cur.execute(
                                "INSERT INTO student_tools (student_id, tool_id) VALUES (%s, %s)",
                                (student_id, tool_id),
                            )
                        for slot in split_values(row["availability"]):
                            slot_id = lookup_id(
                                cur, slots, "availability_slots", "slot_id", "label", slot
                            )
                            cur.execute(
                                "INSERT INTO student_availability (student_id, slot_id) VALUES (%s, %s)",
                                (student_id, slot_id),
                            )

                for table in TABLES:
                    cur.execute(f"SELECT count(*) FROM {table}")
                    print(f"{table}: {cur.fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
