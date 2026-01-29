import json

def extract_test_cases(rows):
    """
    Convert DB rows into test case dicts.
    PostgreSQL JSONB already returns dicts.
    """
    test_cases = []
    for row in rows:
        value = row["result"]

        # SQLite fallback (if ever needed)
        if isinstance(value, str):
            value = json.loads(value)

        test_cases.append(value)

    return test_cases