import os
import time
import pymysql
import pymysql.cursors
from contextlib import contextmanager

DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'inventory_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'inventory_secret')
DB_NAME = os.getenv('DB_NAME', 'inventory_db')


def get_db_connection(max_retries=10, delay=2):
    """
    Establish a connection to the MySQL database with retry backoff.
    Ensures containerized application waits if database container is still booting.
    """
    for attempt in range(1, max_retries + 1):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                charset='utf8mb4'
            )
            return conn
        except pymysql.MySQLError as err:
            if attempt == max_retries:
                print(f"[ERROR] Database connection failed after {max_retries} attempts: {err}")
                raise err
            print(f"[WARN] Database connection attempt {attempt}/{max_retries} failed ({err}). Retrying in {delay}s...")
            time.sleep(delay)


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database cursor handling automatic commit/rollback and cleanup.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def query_db(query, args=(), one=False):
    """
    Executes a SELECT query and returns rows as dictionaries.
    """
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, args)
        result = cursor.fetchall()
        return (result[0] if result else None) if one else result


def execute_db(query, args=()):
    """
    Executes an INSERT, UPDATE, or DELETE query and commits the transaction.
    Returns (lastrowid, rowcount).
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(query, args)
        return cursor.lastrowid, cursor.rowcount
