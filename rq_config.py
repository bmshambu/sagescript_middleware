import os
from redis import Redis
from rq import Queue

redis_conn = Redis(host="localhost", port=6379, db=0)

# REDIS_HOST = "localhost"
# REDIS_PORT =  6379
# REDIS_DB = int(os.getenv("REDIS_DB", 0))

# redis_conn = Redis(
#     host=REDIS_HOST,
#     port=REDIS_PORT,
#     db=REDIS_DB,
#     socket_connect_timeout=5,
#     socket_timeout=5
# )


test_generation_queue = Queue(
    name="functional-test-generation",
    connection=redis_conn
)
