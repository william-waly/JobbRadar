import json
import logging
import os

import requests
from dotenv import load_dotenv
from pydantic import ValidationError

from app.llm.schemas import JobExtraction

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
    truncated_description = description[:3000]  # begrens prompt-størrelse

    prompt = f"{SYSTEM_PROMPT}\n\nTittel: {title}\nBeskrivelse: {truncated_description}"

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": JobExtraction.model_json_schema(),  # tvinger nøyaktig skjema
                "stream": False,
                "options": {"temperature": 0},  # mer deterministisk output
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Kunne ikke nå Ollama: %s", e)
        return None

    raw_output = response.json().get("response", "")

    try:
        parsed = json.loads(raw_output)
        return JobExtraction(**parsed)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning("Ugyldig LLM-output, hopper over: %s", e)
        return None