# geopol_risk.py
# llm geopol analysis with risks to our SC


import time
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

from llm import call_llm_structured
from models import GeopoliticalRiskDigest

load_dotenv()

BASE_URL = "http://localhost:8000"
REPORT_FILE = "geopol_risk_report.txt"

# (connect, read) seconds. The ERP is local so it should answer immediately;
# GDELT is a third party and gets more room.
ERP_TIMEOUT = (5, 15)
GDELT_TIMEOUT = (5, 30)


def fetch_data() -> dict:
    supplier_country = {}
    for supplier in requests.get(f"{BASE_URL}/suppliers", timeout=ERP_TIMEOUT).json():
        country = supplier["country"]
        if country is None:
            continue
        if country not in supplier_country:
            supplier_country[country] = []
        supplier_country[country].append(supplier["name"])
    return supplier_country


COUNTRY_NAMES = {
    "CH": "Switzerland",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "TW": "Taiwan",
    "CN": "China",
    # add as needed
}


def fetch_news(country_code: str) -> list[str]:
    time.sleep(5)  # GDELT rate limits
    country_name = COUNTRY_NAMES.get(country_code, country_code)
    query = (
        f"{country_name} (trade OR tariff OR sanctions OR conflict OR supply chain "
        "OR port OR strike OR war OR tension) sourcelang:english"
    )
    resp = requests.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={
            "query": query,
            "mode": "artlist",
            "maxrecords": 5,
            "sort": "DateDesc",
            "format": "json",
        },
        timeout=GDELT_TIMEOUT,
    )
    if resp.status_code != 200 or not resp.json().get("articles"):
        return []
    return [a["title"] for a in resp.json()["articles"]]


# format data in a prompt for llm analysis
def build_prompt(supplier_country: dict) -> str:
    prompt = (
        "You are a supply chain risk analyst. "
        "Given the following recent news per country, identify geopolitical risks "
        "for our suppliers. Be concise and flag anything actionable.\n\n"
    )
    for country, suppliers in supplier_country.items():
        headlines = fetch_news(country)
        country_name = COUNTRY_NAMES.get(country, country)
        prompt += f"Country: {country_name}\n"
        prompt += f"Our suppliers: {', '.join(suppliers)}\n"
        prompt += "Recent news:\n"
        if headlines:
            for h in headlines:
                prompt += f"  - {h}\n"
        else:
            prompt += "  - No recent news found.\n"
        prompt += "\n"
    return prompt


# llm built report with structured output
def run_report():
    data = fetch_data()
    prompt = build_prompt(data)
    prompt += "\nProvide a structured geopolitical risk assessment with clear country-level analysis and actionable items."

    # Get structured output
    digest = call_llm_structured(prompt, GeopoliticalRiskDigest)

    # Format for output
    formatted = f"""Generated: {digest.timestamp}

GEOPOLITICAL RISK DIGEST
========================

{digest.summary}

"""

    for country in digest.countries:
        formatted += f"\n{country.country.upper()} (Risk Level: {country.risk_level})\n"
        formatted += f"Suppliers: {', '.join(country.suppliers)}\n"
        formatted += "Concerns:\n"
        for concern in country.concerns:
            formatted += f"  • {concern}\n"

    if digest.actionable_items:
        formatted += f"\nACTIONABLE ITEMS:\n"
        for item in digest.actionable_items:
            formatted += f"  → {item}\n"

    with open(REPORT_FILE, "w") as f:
        f.write(formatted)
    print(formatted)


if __name__ == "__main__":
    run_report()
