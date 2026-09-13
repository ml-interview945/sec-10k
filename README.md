# sec-10k

Usage
1. Build the Docker image
docker build -t sec-10k-fetcher .

2. Run
Pass either a company ticker or exact company name:

docker run --rm -v ./output:/app/output sec-10k-fetcher AAPL

For example:

docker run --rm -v ./output:/app/output sec-10k-fetcher MSFT

The generated PDF will be saved to the local output/ directory.
