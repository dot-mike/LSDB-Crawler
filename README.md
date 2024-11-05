# LSDB Crawler

Scrapes LSDB (liveset database) for livesets, events, artists & comments.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/dot-mike/LSDB-Crawler.git
    cd lsdb-crawler
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

To run the scraper, use the following command:
```sh
scrapy crawl liveset_spider
```
