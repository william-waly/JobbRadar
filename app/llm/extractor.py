import json
import logging
import os

import requests
from dotenv import load_dotenv
from pydantic import ValidationError

from app.llm.schemas import JobExtraction
from app.worker.retry import retry_with_backoff

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

SYSTEM_PROMPT = """Du er en assistent som analyserer stillingsannonser.
Basert på tittel og beskrivelse, fyll ut feltene i det oppgitte JSON-skjemaet:
- "category": overordnet jobbkategori (f.eks. "Backend Development", "Sykepleie", "Salg")
- "seniority": ett av "Junior", "Medior", "Senior", "Ukjent"
- "skills": liste med konkrete ferdigheter/teknologier nevnt i teksten (kan være tom liste)"""


def extract_job_info(title: str, description: str) -> JobExtraction | None:
    truncated_description = description[:3000]
    prompt = f"{SYSTEM_PROMPT}\n\nTittel: {title}\nBeskrivelse: {truncated_description}"

    def call_ollama():
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": JobExtraction.model_json_schema(),
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=60,
        )
        response.raise_for_status()
        return response

    response = retry_with_backoff(
        call_ollama,
        max_attempts=3,
        exceptions=(requests.RequestException,),
        label="Ollama-kall",
    )
    if response is None:
        return None  # ga opp etter retries - logget allerede av retry_with_backoff

    raw_output = response.json().get("response", "")

    try:
        parsed = json.loads(raw_output)
        return JobExtraction(**parsed)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning("Ugyldig LLM-output, hopper over (ingen retry - permanent feil): %s", e)
        return None