import json
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


BASE_URL = "https://pam-stilling-feed.nav.no"

MAX_PAGES = 100
START_DATE = datetime(2026, 8, 1, tzinfo=timezone.utc)
END_DATE = datetime(2026, 9, 10, 23, 59, 59, tzinfo=timezone.utc)


# ---------------------------------------------------------
# Søkeord som må finnes i STILLINGSTITTELEN
# ---------------------------------------------------------

TITLE_KEYWORDS = [
    "utvikler",
    "developer",
    "programmerer",
    "software engineer",
    "software developer",
    "systemutvikler",
    "frontend",
    "backend",
    "fullstack",
    "full stack",
    "data engineer",
    "devops",
    "programvareutvikler",
    "webutvikler",
    "javautvikler",
    "pythonutvikler",
    ".net-utvikler",
]


# ---------------------------------------------------------
# Byer
# ---------------------------------------------------------

LOCATIONS = [
    "bergen",
    "stavanger",
    "sandnes",
    "trondheim",
    "oslo",
]


# ---------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------

def make_url(path):
    if not path:
        return None

    if path.startswith("http"):
        return path

    if path.startswith("/"):
        return BASE_URL + path

    return BASE_URL + "/" + path


def relevant_title(title):
    """
    Sjekker KUN stillingstittelen.
    """

    title = title.lower()

    return any(
        keyword.lower() in title
        for keyword in TITLE_KEYWORDS
    )


def relevant_location(location):
    """
    Sjekker om kommunen/stedet er en av
    stedene vi ønsker.
    """

    location = location.lower()

    return any(
        city.lower() in location
        for city in LOCATIONS
    )

def get_ad_details(feed_url, headers):
    req = urllib.request.Request(
        feed_url,
        headers=headers
    )

    with urllib.request.urlopen(req) as response:
        detail = json.loads(
            response.read().decode("utf-8")
        )

    # NAV kan returnere data under ad_content
    if isinstance(detail.get("ad_content"), dict):
        return detail["ad_content"]

    # Eller under json
    if isinstance(detail.get("json"), dict):
        return detail["json"]

    return detail

# ---------------------------------------------------------
# Hent token
# ---------------------------------------------------------

token_url = f"{BASE_URL}/api/publicToken"

with urllib.request.urlopen(token_url) as response:
    token = (
        response
        .read()
        .decode("utf-8")
        .strip()
        .splitlines()[-1]
        .strip()
    )

print("Token hentet.")
print()


headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
}


# ---------------------------------------------------------
# Startdato
# ---------------------------------------------------------

start_date = START_DATE

if_modified_since = format_datetime(start_date)

print(
    f"Henter annonser endret siden: "
    f"{if_modified_since}"
)

print()


# ---------------------------------------------------------
# Hent feed
# ---------------------------------------------------------

current_url = f"{BASE_URL}/api/v1/feed"

pages_checked = 0
active_items = 0
relevant_items = 0

ads = {}


while current_url and pages_checked < MAX_PAGES:

    print(
        f"Sjekker feed-side "
        f"{pages_checked + 1}..."
    )

    request_headers = headers.copy()

    if pages_checked == 0:
        request_headers["If-Modified-Since"] = (
            if_modified_since
        )

    req = urllib.request.Request(
        current_url,
        headers=request_headers
    )

    try:

        with urllib.request.urlopen(req) as response:

            feed_data = json.loads(
                response
                .read()
                .decode("utf-8")
            )

    except Exception as e:

        print(
            f"Feil ved henting av feed: {e}"
        )

        break

    pages_checked += 1

    items = feed_data.get(
        "items",
        []
    )

    print(
        f"  {len(items)} items"
    )


    # -----------------------------------------------------
    # Gå gjennom ALLE items på siden
    # -----------------------------------------------------

    for item in items:
        modified_text = item.get("date_modified")

        if not modified_text:
            continue

        try:
            modified_date = datetime.fromisoformat(
                modified_text.replace("Z", "+00:00")
            )
        except ValueError:
            continue

        if modified_date < START_DATE:
            continue

        if modified_date > END_DATE:
            continue
        
        feed_entry = item.get("_feed_entry", {})
        
        status = feed_entry.get(
            "status",
            ""
        ).upper()


        # -------------------------------------------------
        # Kun aktive annonser
        # -------------------------------------------------

        if status != "ACTIVE":
            continue

        active_items += 1


        # -------------------------------------------------
        # ID
        # -------------------------------------------------

        ad_id = (
            feed_entry.get("uuid")
            or item.get("id")
        )

        if not ad_id:
            continue


        # -------------------------------------------------
        # Tittel
        # -------------------------------------------------

        title = item.get(
            "title",
            ""
        )


        # -------------------------------------------------
        # Sjekk stillingstittel
        # -------------------------------------------------

        if not relevant_title(title):
            continue


        # -------------------------------------------------
        # Arbeidsgiver
        # -------------------------------------------------

        employer = feed_entry.get(
            "businessName",
            "Ukjent arbeidsgiver"
        )


        # -------------------------------------------------
        # Sted
        # -------------------------------------------------

        municipality = feed_entry.get(
            "municipal",
            "Ukjent sted"
        )


        # -------------------------------------------------
        # Sjekk sted
        # -------------------------------------------------

        if not relevant_location(
            municipality
        ):
            continue


        relevant_items += 1


        # -------------------------------------------------
        # Lagre annonsen
        # -------------------------------------------------

        ads[ad_id] = {
            "id": ad_id,
            "title": title,
            "employer": employer,
            "location": municipality,
            "status": status,
            "modified": feed_entry.get(
                "sistEndret",
                "Ukjent"
            ),
            "public_url": make_url(
                f"https://arbeidsplassen.nav.no/stillinger/stilling/{ad_id}"
            ),
        }


    # -----------------------------------------------------
    # Neste side
    # -----------------------------------------------------

    next_url = feed_data.get(
        "next_url"
    )

    if not next_url:
        break

    current_url = make_url(
        next_url
    )


# ---------------------------------------------------------
# RESULTAT
# ---------------------------------------------------------

print()

print("=" * 70)
print("RESULTAT")
print("=" * 70)

print(
    f"Feed-sider sjekket: "
    f"{pages_checked}"
)

print(
    f"Aktive feed-items: "
    f"{active_items}"
)

print(
    f"Relevante feed-items: "
    f"{relevant_items}"
)

print(
    f"Unike relevante annonser: "
    f"{len(ads)}"
)

print()


# ---------------------------------------------------------
# Skriv ut annonser
# ---------------------------------------------------------

for number, ad in enumerate(
    ads.values(),
    start=1
):

    print("-" * 70)

    print(
        f"#{number}"
    )

    print(
        f"Tittel:       "
        f"{ad['title']}"
    )

    print(
        f"Arbeidsgiver: "
        f"{ad['employer']}"
    )

    print(
        f"Sted:         "
        f"{ad['location']}"
    )

    print(
        f"Status:       "
        f"{ad['status']}"
    )

    print(
        f"Sist endret:  "
        f"{ad['modified']}"
    )

    print(
        f"Feed URL:     "
        f"{ad['public_url']}"
    )


print()

print("=" * 70)
print("FERDIG")
print("=" * 70)