import os
import json
import logging
import google.generativeai as genai
from state import DecisionOutput
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_llm_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    return genai.GenerativeModel(model_name)


def normalize_llm_response(result: dict) -> dict:
    """Normalize LLM response to match expected schema"""
    # Handle case where 'why' is returned as a list instead of string
    if "why" in result and isinstance(result["why"], list):
        # Convert list to bullet-point string
        result["why"] = "\n".join(
            f"- {item.strip()}" for item in result["why"] if item.strip()
        )

    # Convert INSUFFICIENT_DATA to HOLD with appropriate messaging
    if result.get("decision") == "INSUFFICIENT_DATA":
        result["decision"] = "HOLD"
        if "why" in result:
            result[
                "why"
            ] += "\n- Decision based on limited available data; HOLD recommended as conservative approach."
        else:
            result["why"] = (
                "Decision based on limited available data; HOLD recommended as conservative approach."
            )
        # Reduce confidence to reflect uncertainty
        result["confidence"] = min(result.get("confidence", 0.5), 0.4)

    # Ensure other fields are in correct format
    for field in [
        "key_factors",
        "risks",
        "personalization_considerations",
        "used_agents",
        "citations",
    ]:
        if field in result and not isinstance(result[field], list):
            result[field] = []

    return result


def call_llm(system_prompt: str, user_prompt: str) -> dict:
    logger.info("Calling Gemini LLM for decision analysis")

    model = get_llm_client()

    full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nOutput JSON only:"

    try:
        logger.info("Making initial LLM call")
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1, response_mime_type="application/json"
            ),
        )

        logger.info(f"LLM response received: {response.text[:500]}...")
        result = json.loads(response.text)

        # Normalize the response
        result = normalize_llm_response(result)

        # Validate with Pydantic
        DecisionOutput(**result)
        logger.info("LLM response successfully validated")
        return result

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Initial LLM call failed: {e}. Attempting retry...")

        # Retry with strict JSON prompt
        retry_prompt = "Return JSON only. No prose.\n" + user_prompt
        try:
            response = model.generate_content(
                retry_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.0, response_mime_type="application/json"
                ),
            )

            logger.info(f"Retry LLM response received: {response.text[:500]}...")
            result = json.loads(response.text)

            # Normalize the response
            result = normalize_llm_response(result)

            # Validate with Pydantic
            DecisionOutput(**result)
            logger.info("Retry LLM response successfully validated")
            return result

        except Exception as retry_e:
            logger.error(f"Retry LLM call also failed: {retry_e}")
            logger.error(
                f"Raw LLM response: {response.text if 'response' in locals() else 'No response'}"
            )
            raise retry_e
