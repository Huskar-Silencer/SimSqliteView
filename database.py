import sqlite3
from typing import Optional


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self):
        self._connection: Optional[sqlite3.Connection] = None
        self._db_path: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None

    @property
    def db_path(self) -> Optional[str]:
        return self._db_path

    def connect(self, db_path: str) -> None:
        """Open a connection to the SQLite database file."""
        self.close()
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._db_path = db_path

    def close(self) -> None:
        """Close the current database connection and reset state."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._db_path = None

    def execute_query(self, sql: str, params: tuple = ()) -> tuple[list, list[str]]:
        """Execute a SQL query and return (rows, column_names)."""
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            # Convert Row objects to tuples
            rows = [tuple(row) for row in rows]
            return rows, columns
        return [], []

    def execute_script(self, sql: str) -> tuple[list, list[str], int]:
        """Execute SQL script (may contain multiple statements).
        Returns (rows, columns, rowcount) for the last statement."""
        cursor = self._connection.cursor()
        cursor.executescript(sql)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            rows = [tuple(row) for row in rows]
            return rows, columns, cursor.rowcount
        return [], [], cursor.rowcount

    def get_tables(self) -> list[str]:
        """Get all table names in the database."""
        rows, _ = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in rows]

    def get_views(self) -> list[str]:
        """Get all view names in the database."""
        rows, _ = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        )
        return [row[0] for row in rows]

    def get_indexes(self) -> list[str]:
        """Get all index names in the database."""
        rows, _ = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        return [row[0] for row in rows]

    def get_triggers(self) -> list[str]:
        """Get all trigger names in the database."""
        rows, _ = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name"
        )
        return [row[0] for row in rows]

    def get_table_info(self, table_name: str) -> list[dict]:
        """Get column information for a table."""
        rows, _ = self.execute_query(f"PRAGMA table_info('{table_name}')")
        columns = []
        for row in rows:
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default_value": row[4],
                "pk": row[5],
            })
        return columns

    def get_table_data(self, table_name: str, limit: int = 1000, offset: int = 0) -> tuple[list, list[str]]:
        """Get data from a table with optional limit and offset."""
        return self.execute_query(
            f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {offset}'
        )

    def get_row_count(self, table_name: str) -> int:
        """Get the total number of rows in a table."""
        rows, _ = self.execute_query(f'SELECT COUNT(*) FROM "{table_name}"')
        return rows[0][0] if rows else 0

    def get_create_sql(self, name: str) -> str:
        """Get the CREATE SQL statement for a database object."""
        rows, _ = self.execute_query(
            "SELECT sql FROM sqlite_master WHERE name=?", (name,)
        )
        return rows[0][0] if rows and rows[0][0] else ""

    def get_all_objects(self) -> list[dict]:
        """Get all database objects (tables, views, indexes, triggers)."""
        rows, _ = self.execute_query(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        )
        objects = []
        for row in rows:
            objects.append({
                "type": row[0],
                "name": row[1],
                "table": row[2],
                "sql": row[3] or "",
            })
        return objects

    def get_table_indexes(self, table_name: str) -> list[dict]:
        """Get index information for a specific table."""
        rows, _ = self.execute_query(f"PRAGMA index_list('{table_name}')")
        indexes = []
        for row in rows:
            idx_name = row[1]
            unique = row[2]
            # Get columns in this index
            idx_rows, _ = self.execute_query(f"PRAGMA index_info('{idx_name}')")
            idx_cols = [r[2] for r in idx_rows]
            indexes.append({
                "name": idx_name,
                "unique": unique,
                "columns": idx_cols,
            })
        return indexes

    def get_foreign_keys(self, table_name: str) -> list[dict]:
        """Get foreign key information for a specific table."""
        rows, _ = self.execute_query(f"PRAGMA foreign_key_list('{table_name}')")
        fks = []
        for row in rows:
            fks.append({
                "id": row[0],
                "seq": row[1],
                "table": row[2],
                "from": row[3],
                "to": row[4],
                "on_update": row[5],
                "on_delete": row[6],
            })
        return fks

    def get_table_size(self, table_name: str) -> int:
        """Estimate the size of a table in bytes using page_count and page_size."""
        try:
            rows, _ = self.execute_query(
                f'SELECT SUM(LENGTH(CAST("{table_name}" AS TEXT))) FROM "{table_name}"'
            )
            return rows[0][0] if rows and rows[0][0] else 0
        except Exception:
            return 0
