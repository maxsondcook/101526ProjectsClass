"""Run starter queries against the intake database.

With no arguments, runs the sample queries below.
Pass a SQL string to run that instead:

    python query_db.py "SELECT name, netid FROM students ORDER BY name"
"""

import os
import sys

import psycopg2

from load_data import ROOT, load_dotenv

QUERIES = (
    (
        "Student count",
        "SELECT count(*) AS n_students FROM students",
    ),
    (
        "Five students and their school year",
        """
        SELECT s.name, y.label AS school_year
        FROM students s
        JOIN school_years y ON s.school_year_id = y.school_year_id
        ORDER BY s.name
        LIMIT 5
        """,
    ),
    (
        "Tools by number of students",
        """
        SELECT t.name, COUNT(*) AS n_students
        FROM student_tools st
        JOIN tools t ON st.tool_id = t.tool_id
        GROUP BY t.name
        ORDER BY n_students DESC
        """,
    ),
    (
        "Availability by number of students",
        """
        SELECT a.label, COUNT(*) AS n_students
        FROM student_availability sa
        JOIN availability_slots a ON sa.slot_id = a.slot_id
        GROUP BY a.label
        ORDER BY n_students DESC
        """,
    ),
    (
        "Students by intro programming background",
        """
        SELECT p.code, COUNT(*) AS n_students
        FROM students s
        JOIN intro_programming p ON s.intro_programming_id = p.intro_programming_id
        GROUP BY p.code
        ORDER BY n_students DESC
        """,
    ),
)


def connect():
    load_dotenv(ROOT / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is missing from .env")
    if "railway.internal" in database_url:
        raise SystemExit(
            "DATABASE_URL uses the private Railway host (railway.internal). "
            "Use DATABASE_PUBLIC_URL from the laptop."
        )
    return psycopg2.connect(database_url)


def print_result(cur) -> None:
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    widths = [len(column) for column in columns]
    rendered = []
    for row in rows:
        cells = ["" if value is None else str(value) for value in row]
        rendered.append(cells)
        widths = [max(width, len(cell)) for width, cell in zip(widths, cells)]

    header = "  ".join(column.ljust(width) for column, width in zip(columns, widths))
    print(header)
    print("  ".join("-" * width for width in widths))
    for cells in rendered:
        print("  ".join(cell.ljust(width) for cell, width in zip(cells, widths)))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def main() -> None:
    if len(sys.argv) > 1:
        queries = (("custom", " ".join(sys.argv[1:])),)
    else:
        queries = QUERIES

    conn = connect()
    try:
        with conn:
            with conn.cursor() as cur:
                for title, sql in queries:
                    print(f"\n== {title} ==")
                    cur.execute(sql)
                    if cur.description is None:
                        print(f"done ({cur.rowcount} rows affected)")
                    else:
                        print_result(cur)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
