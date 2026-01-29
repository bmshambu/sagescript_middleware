from schemas.test_case import TestCasesSchema,TestCase
import json
import random

def store_test_cases(test_Cases: str ):
    """
    Validates and stores LLM output (test_Cases) as a JSON file.

    :param test_Cases: JSON string containing test case data.

    """
    thread_id = random.randint(1, 1000000)
    file_path: str = f"test_cases_{thread_id}.json"
    try:
        test_cases_data = json.loads(test_Cases)  # Convert string JSON to Python dict
        validated_data = TestCasesSchema(**test_cases_data)  # Validate with Pydantic

        with open(file_path, "w") as file:
            json.dump(validated_data.dict(), file, indent=4)

        print(f"Test cases stored successfully in {file_path}")

    except Exception as e:
        print(f"Error storing test cases: {e}")