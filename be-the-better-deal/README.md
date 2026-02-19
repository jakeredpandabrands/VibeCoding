# Be the Better Deal

Track your Amazon product’s pricing and deals against competitors. Enter your ASIN, add competing ASINs, and run periodic checks to see where you stand.

## Current Features

- **Product & competitor setup** — Enter your product’s Amazon ASIN and a list of competing ASINs
- **Manual trigger** — Run a check whenever you want (daily automation coming soon)
- **Price logging** — For each ASIN, fetches current price and records date + price in the database
- **Deal & coupon capture** — Records deal type (e.g., Lightning Deal, Today’s Deal) and any coupon amounts/details when available

All data is logged over time so you can see how prices and offers change for you and your competitors.

## Future Features

- Run simple but helpful analysis on the collected data
- Send text or email alerts when a competitor changes anything about their deal (price, coupon, etc.)
- Add keyword tracking for page rank of given keyword *(probably a much bigger project, not a fast follow)*
- Add overall BSR tracking *(potentially easier than page ranking — maybe a fast follow, maybe not)*

## Quick Start

```bash
cd be-the-better-deal
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser.

## Note on Amazon Data

The app currently uses **mock data** for development. To connect to real Amazon data, you’ll need to wire in a data source in `amazon.py` — e.g. [Keepa](https://keepa.com/#!api), [Rainforest API](https://www.rainforestapi.com/), Product Advertising API, or a custom scraper.
