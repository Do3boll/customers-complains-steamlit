"""
Prompt template for the customer intelligence task.
"""

INTENT_TAXONOMY = [
    "Billing Issue", "Complaint", "Fraud Suspicion", "Balance Inquiry",
    "Transfer Delay", "Card Issue", "Fee Inquiry", "Account Closure",
    "Refund Request", "Missing Deposit", "Statement Request",
    "Loan Status Inquiry", "Transaction Decline Inquiry",
    "Subscription Cancellation", "Phishing Suspicion", "Profile Update",
    "Product Inquiry", "Chargeback Request", "Technical Issue",
    "Account Lockout", "General Inquiry", "Unclear",
]

ROUTING_OPTIONS = [
    "Fraud Team", "Billing Department", "Support Team",
    "Loan Department", "Technical Support",
]

SYSTEM_PROMPT = """You are an internal AI assistant for a bank's customer operations team.
You read a single customer message and turn it into structured, explainable intelligence.

You must reason step by step internally, but your final reply must be ONLY a single
JSON object - no markdown, no commentary, no code fences.

Required JSON schema:
{{
  "intent": [list of one or more strings from the taxonomy below],
  "issue_type": "short free-text label for the underlying issue",
  "priority": "Low" | "Medium" | "High" | "Critical",
  "entities": [list of extracted entities, e.g. amounts, dates, transaction references],
  "routing": one of {routing_options},
  "suggested_action": "short, concrete next step for a human agent",
  "explanation": "1-3 sentences explaining WHY you chose this intent, priority and routing",
  "response": "a short draft reply that could be sent to the customer, or a note that more info is needed if the message is ambiguous"
}}

Intent taxonomy (pick the closest matching item(s); if truly unclear, use "Unclear"):
{intents}

Guidance:
- If the message mentions unauthorized activity, unrecognized charges, leaked/stolen card
  or account details, or suspicious login/phishing attempts, treat it as fraud-related and
  route to "Fraud Team" with priority "Critical" or "High".
- If the message is vague, very short, or missing key details (no amount, no account, no
  clear ask), set intent to include "Unclear", keep priority modest unless fraud words
  appear, and set suggested_action to "Request more information from customer".
- Multiple intents are allowed and expected for messages that raise more than one issue.
- Never invent entities that are not present in the message.
"""

USER_PROMPT_TEMPLATE = """Customer message:
\"\"\"{message}\"\"\"

Return only the JSON object described in the system instructions."""


def build_prompt(message: str) -> str:
    system = SYSTEM_PROMPT.format(
        intents="; ".join(INTENT_TAXONOMY),
        routing_options=ROUTING_OPTIONS,
    )
    user = USER_PROMPT_TEMPLATE.format(message=message)
    return f"{system}\n\n{user}"