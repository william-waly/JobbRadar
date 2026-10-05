import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


def retry_with_backoff[T](
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    label: str = "operasjon",
) -> T | None:
    """
    Kjører func() med inntil max_attempts forsøk og eksponentiell backoff
    (1s, 2s, 4s, ...) mellom hvert forsøk. Returnerer None hvis alle
    forsøk feiler, i stedet for å la unntaket forplante seg videre.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts:
                logger.error(
                    "%s feilet etter %d forsøk: %s", label, max_attempts, e
                )
                return None
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "%s feilet (forsøk %d/%d): %s. Prøver igjen om %.0fs.",
                label, attempt, max_attempts, e, delay,
            )
            time.sleep(delay)
    return None