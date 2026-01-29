
from typing import List, Dict, Any

def summarize_test_case_priorities(test_cases: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Summarize the number of test cases by their priority levels.
    Args:

        test_cases (List[Dict[str, Any]]): A list of test case dictionaries, each containing a "Priority" key.
    Returns:

        Dict[str, int]: A dictionary with counts of high, medium, and low priority test cases.
    """
    if not test_cases:
        return {"high": 0, "medium": 0, "low": 0}
    high = 0
    medium = 0
    low = 0
    for tc in test_cases:
        priority = tc.get("Priority", "").lower()
        if priority == "high":
            high += 1
        elif priority == "medium":
            medium += 1
        elif priority == "low":
            low += 1
    print(f"Priority Summary - High: {high}, Medium: {medium}, Low: {low}")
    return {"high": high, "medium": medium, "low": low}
