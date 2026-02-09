#import json

# def extract_test_cases(rows):
#     """
#     Convert DB rows into test case dicts.
#     PostgreSQL JSONB already returns dicts.
#     """
#     test_cases = []
#     for row in rows:
#         value = row["result"]

#         # SQLite fallback (if ever needed)
#         if isinstance(value, str):
#             value = json.loads(value)

#         test_cases.append(value)

#     return test_cases

import json
from typing import Any, List, Dict

def extract_test_cases(rows: List[Any]) -> List[Dict[str, Any]]:
    """
    Convert DB rows into a flat list of test case dicts.
    Handles nested lists and JSON strings from Postgres/SQLite.
    """
    test_cases: List[Dict[str, Any]] = []

    def flatten(item):
        if isinstance(item, list):
            for sub in item:
                flatten(sub)
        elif isinstance(item, dict):
            test_cases.append(item)
        elif isinstance(item, str):
            # JSON fallback (SQLite or misconfigured driver)
            try:
                parsed = json.loads(item)
                flatten(parsed)
            except json.JSONDecodeError:
                pass

    for row in rows:
        # Case 1: Postgres returns directly nested list
        if isinstance(row, (list, dict, str)):
            flatten(row)

        # Case 2: row is a record with "result" column
        elif isinstance(row, dict) and "result" in row:
            flatten(row["result"])

    return test_cases
