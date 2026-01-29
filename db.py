import os
import psycopg
from psycopg.rows import dict_row
#from config import AppConfig
#cfg =AppConfig()
import os
def get_connection():
    return psycopg.connect(
        os.environ["database_url"],
        row_factory=dict_row
    )




