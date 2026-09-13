# sec-10k

Usage
1. Clone the repo

`git clone https://github.com/ml-interview945/sec-10k`

2. Build the Docker image:
   
`docker build -t sec-10k-fetcher .`

3. Run
Pass either a company ticker or exact company name:

`docker run --rm -v ./output:/app/output sec-10k-fetcher AAPL`

The generated PDF will be saved to the local output/ directory.
