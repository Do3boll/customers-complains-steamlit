"""
Runs every message in dataset.csv through the LLM pipelin and writes results.csv
"""

import csv
import json
import logging

from prompts import build_prompt
from llm import generate_json
from api import _normalize_llm_output

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("customer_intelligence.batch")


def main():
    with open("dataset.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    for row in rows:
        message = row["message"]
        try:
            raw = generate_json(build_prompt(message))
            output = _normalize_llm_output(raw)
            error = ""
        except Exception as e:
            logger.warning("id=%s failed: %s", row["id"], e)
            output = {
                "intent": [], "issue_type": "", "priority": "",
                "entities": [], "routing": "", "suggested_action": "",
                "explanation": "", "response": "",
            }
            error = str(e)

        results.append({
            "id": row["id"],
            "message": message,
            "expected_intent": row["expected_intent"],
            "expected_priority": row["expected_priority"],
            "expected_routing": row["expected_routing"],
            "predicted_intent": ";".join(output["intent"]),
            "predicted_priority": output["priority"],
            "predicted_routing": output["routing"],
            "predicted_entities": ";".join(output["entities"]),
            "suggested_action": output["suggested_action"],
            "explanation": output["explanation"],
            "response": output["response"],
            "error": error,
        })

    fieldnames = list(results[0].keys())
    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Processed {len(results)} messages -> results.csv")


if __name__ == "__main__":
    main()