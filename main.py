import requests
from weasyprint import HTML
import sys
import os

HTTP_HEADERS = {"User-Agent": "Marcus Linderholm marcus.linderholm@gmail.com"}


def format_accession_number(unformatted_accession_number: str) -> str:
    return unformatted_accession_number.replace("-", "")


def format_cik(unformatted_cik: int) -> str:
    return f"CIK{unformatted_cik:010d}"


def sec_request(url: str):
    response = requests.get(url, headers=HTTP_HEADERS, timeout=60)
    response.raise_for_status()
    return response


def fetch_company_tickers_exchange() -> dict:
    return sec_request(
        f"https://www.sec.gov/files/company_tickers_exchange.json"
    ).json()


def save_file_to_pdf(url: str, output_file_name: str) -> None:
    file = sec_request(url)
    print(f"Downloaded: {len(file.content)} bytes")
    HTML(string=file.text, base_url=url).write_pdf(output_file_name)
    print(f"PDF generated: {output_file_name}")


def get_file_url(cik: int, accession_number: str) -> str:
    file = sec_request(
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}.txt"
    ).text.split("\n")
    file_name = None

    # This seems like a hack, but couldnt find a more appropriate endpoint
    for line in file:
        if "<FILENAME>" in line:
            file_name = line.split("<FILENAME>")[1]
            break
    else:
        raise Exception("No file name found in accession file")

    print(f"File name: {file_name}")

    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{format_accession_number(accession_number)}/{file_name}"


def get_most_recent_filing(cik: int, form: str) -> tuple[str, str]:
    submissions = sec_request(
        f"https://data.sec.gov/submissions/{format_cik(cik)}.json"
    ).json()

    filings = submissions["filings"]["recent"]

    indices = [i for i, form_id in enumerate(filings["form"]) if form_id == form]

    if not indices:
        raise ValueError("Did not find form")

    # Fairly certain these are always in order, but incase they aren't we sort them
    most_recent_index = max(indices, key=lambda i: filings["filingDate"][i])

    return (
        filings["accessionNumber"][most_recent_index],
        filings["filingDate"][most_recent_index],
    )


def get_cik_for_company(identifier: str):
    company_tickers_exchange = fetch_company_tickers_exchange()
    fields = company_tickers_exchange["fields"]
    data = company_tickers_exchange["data"]
    cik_index, name_index, ticker_index = [
        fields.index(label) for label in ["cik", "name", "ticker"]
    ]
    identifier = identifier.strip().upper()
    for item in data:
        name = item[name_index].upper()
        ticker = item[ticker_index].upper()

        if identifier == name or identifier == ticker:
            cik = item[cik_index]
            print(f"CIK found for {item[name_index]}: {cik}")
            return cik, item[name_index], item[ticker_index]

    raise Exception(f"No CIK found for {identifier}")


def download_most_recent_filing_for_company(identifier: str, form: str, output_file_name: str = None):
    cik, company_name, company_ticker = get_cik_for_company(identifier)
    accession_number, filing_date = get_most_recent_filing(cik, form)
    file_url = get_file_url(cik, accession_number)
    file_name = output_file_name or f"{company_ticker}-{form}-{filing_date}.pdf"
    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", file_name)
    save_file_to_pdf(file_url, output_path)

    return {
        "CIK": cik,
        "Company Name": company_name,
        "PDF File Name": output_path,
        "Accession Number": accession_number,
        "Filing Date": filing_date,
        "URL": file_url,
    }


if __name__ == "__main__":
    try:
        identifier = sys.argv[1]
    except IndexError as e:
        identifier = input(
            "Provide an exact company name(or ticker) to fetch 10-K filing for:\n"
        )

    try:
        output = download_most_recent_filing_for_company(identifier, '10-K')
        print("Finished generating 10-K pdf:")
        for key, val in output.items():
            print(f"    {key}: {val}")
    except Exception as e:
        print(e)
