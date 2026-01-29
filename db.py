import os
import psycopg
from psycopg.rows import dict_row
from config import AppConfig
cfg =AppConfig()
def get_connection():
    return psycopg.connect(
        cfg.database_url,
        row_factory=dict_row
    )




