"""
huggingface-cli login
"""

import os
import json
import logging

from huggingface_hub import InferenceClient

logger = logging.getLogger("customer_intelligence.llm")

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN") or "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"
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "openai/gpt-oss-20b")
HF_PROVIDER = os.getenv("HF_PROVIDER", "auto") 

if not HF_TOKEN:
    raise RuntimeError(
        "No Hugging Face token found. Set the HF_TOKEN environment variable "
        "to your Hugging Face access token (https://huggingface.co/settings/tokens)."
    )

_client = InferenceClient(model=HF_MODEL_ID, token=HF_TOKEN, provider=HF_PROVIDER)



def generate(prompt: str, max_new_tokens: int = 700, temperature: float = 0.0) -> str:
    #Send a prompt to the Hugging Face Inference API and return raw text.
    logger.info("Calling HF Inference API model=%s", HF_MODEL_ID)
    try:
        result = _client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_new_tokens,
            temperature=temperature,
        )
        return result.choices[0].message.content
    except Exception:
        logger.warning("chat_completion failed, falling back to text_generation")
       
        return _client.text_generation(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature if temperature > 0 else 0.01,
        )


def generate_json(prompt: str, max_retries: int = 2) -> dict:
    """
    Call the model and force a JSON dict out of it.
    Retries with a stricter reminder if the first parse fails.
    """
    last_error = None
    current_prompt = prompt
    for attempt in range(max_retries + 1):
        raw = generate(current_prompt)
        cleaned = raw.strip()

        # strip markdown code fences if the model wraps its output
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning("JSON parse failed on attempt %d: %s", attempt + 1, e)
            current_prompt = (
                prompt
                + "\n\nYour previous reply was not valid JSON. "
                + "Reply again with ONLY a single valid JSON object, no extra text, no markdown."
            )
    raise ValueError(f"Model did not return valid JSON after retries: {last_error}")

if __name__ == "__main__":
    test_message = "I was charged twice for the same transaction and I need this resolved immediately."
    print(f"Model: {HF_MODEL_ID}")
    print(f"Sending test message: {test_message!r}\n")
    print("Raw generate() output:")
    print(generate(f"Reply with one short sentence: {test_message}"))