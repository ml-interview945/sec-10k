import requests
from weasyprint import HTML
import sys
import os

class SECFormFetcher:
    def __init__(self, identifier, form, user_agent, output_file_name = None):
        self.identifier = identifier
        self.form = form
        self.output_file_name = output_file_name
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": user_agent}
        )


    @staticmethod
    def format_accession_number(unformatted_accession_number: str) -> str:
        return unformatted_accession_number.replace("-", "")


    @staticmethod
    def format_cik(unformatted_cik: int) -> str:
        return f"CIK{unformatted_cik:010d}"


    def sec_request(self, url: str):
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        return response


    def fetch_company_tickers_exchange(self) -> dict:
        return self.sec_request(
            f"https://www.sec.gov/files/company_tickers_exchange.json"
        ).json()


    def save_file_to_pdf(self, url: str, output_file_name: str) -> None:
        file = self.sec_request(url)
        print(f"Downloaded: {len(file.content)} bytes")
        HTML(string=file.text, base_url=url).write_pdf(output_file_name)
        print(f"PDF generated: {output_file_name}")


    def get_file_url(self, cik: int, accession_number: str, file_name: str) -> str:
        return f"https://www.sec.gov/Archives/edgar/data/{cik}/{self.format_accession_number(accession_number)}/{file_name}"


    def get_most_recent_filing(self, cik: int) -> tuple[str, str, str]:
        submissions = self.sec_request(
            f"https://data.sec.gov/submissions/{self.format_cik(cik)}.json"
        ).json()

        filings = submissions["filings"]["recent"]

        indices = [i for i, form_id in enumerate(filings["form"]) if form_id == self.form]

        if not indices:
            raise ValueError("Did not find form")

        # Fairly certain these are always in order, but incase they aren't we sort them
        most_recent_index = max(indices, key=lambda i: filings["filingDate"][i])
        return (
            filings["accessionNumber"][most_recent_index],
            filings["filingDate"][most_recent_index],
            filings["primaryDocument"][most_recent_index]
        )


    def get_cik_for_company(self):
        company_tickers_exchange = self.fetch_company_tickers_exchange()
        fields = company_tickers_exchange["fields"]
        data = company_tickers_exchange["data"]
        cik_index, name_index, ticker_index = [
            fields.index(label) for label in ["cik", "name", "ticker"]
        ]
        identifier = self.identifier.strip().upper()
        for item in data:
            name = item[name_index].upper()
            ticker = item[ticker_index].upper()

            if identifier == name or identifier == ticker:
                cik = item[cik_index]
                print(f"CIK found for {item[name_index]}: {cik}")
                return cik, item[name_index], item[ticker_index]

        raise Exception(f"No CIK found for {identifier}")


    def download_latest_filing(self):
        cik, company_name, company_ticker = self.get_cik_for_company()
        accession_number, filing_date, file_name = self.get_most_recent_filing(cik)
        file_url = self.get_file_url(cik, accession_number, file_name)
        file_name = self.output_file_name or f"{company_ticker}-{self.form}-{filing_date}.pdf"
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", file_name)
        self.save_file_to_pdf(file_url, output_path)

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
        sec_10_k_form_fetcher = SECFormFetcher(
            identifier=identifier,
            form='10-K',
            user_agent='Marcus Linderholm marcus.linderholm@gmail.com',
        )
        output = sec_10_k_form_fetcher.download_latest_filing()
        print("Finished generating 10-K pdf:")
        for key, val in output.items():
            print(f"    {key}: {val}")
    except Exception as e:
        print(e)
