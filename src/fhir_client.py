import requests


FHIR_BASE_URL = "https://hapi.fhir.org/baseR4"


def get_patients():
    url = f"{FHIR_BASE_URL}/Patient"

    params = {
        "_count": 5
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_next_link(bundle):
    links = bundle.get("link", [])

    for link in links:
        if link.get("relation") == "next":
            return link.get("url")

    return None

def get_page(url):
    response = requests.get(url, timeout=10)

    response.raise_for_status()

    return response.json()

def get_patient_pages(max_pages=3):
    bundle = get_patients()
    page_number = 1

    while bundle and page_number <= max_pages:
        yield bundle

        next_url = get_next_link(bundle)

        if not next_url:
            break

        bundle = get_page(next_url)
        page_number += 1