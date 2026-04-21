from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from app.core.config import settings
import logging

logger = logging.getLogger("db")

class Database:
    _pool: ConnectionPool = None

    @classmethod
    def initialize(cls):
        if cls._pool is None:
            logger.info("Initializing Database Connection Pool...")
            conn_args = {
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
            
            try:
                cls._pool = ConnectionPool(
                    conninfo=(
                        f"dbname={settings.DB_NAME} "
                        f"user={settings.DB_USER} "
                        f"password={settings.DB_PASS} "
                        f"host={settings.DB_HOST} "
                        f"port={settings.DB_PORT}"
                    ),
                    min_size=1,
                    max_size=10,
                    timeout=30,
                    kwargs=conn_args
                )
                logger.info(f"Database Connection Pool Initialized Successfully. with settings: {settings.DB_NAME}, {settings.DB_USER}, {settings.DB_HOST}, {settings.DB_PORT}")
            except Exception as e:
                logger.error(f"DB Connection Failed: {e}")
                raise

    @classmethod
    def close(cls):
        if cls._pool:
            cls._pool.close()

    @classmethod
    @contextmanager
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize()
        
        with cls._pool.connection() as conn:
            yield conn