# Crypto Price Bot

A Telegram bot that provides real-time cryptocurrency price updates and notifications. The bot tracks major cryptocurrencies including Bitcoin, Ethereum, Solana, ATOM, Aptos, SUI, Arbitrum, Optimism, and Polygon.

## Features

- Real-time price updates every 30 minutes
- Support for multiple cryptocurrencies
- Price change notifications with 24h changes
- Market cap and volume information
- Easy-to-use commands for price checks

## Commands

- `/p <symbol>` or `/price <symbol>` - Get the current price of a cryptocurrency
  Example: `/p btc` or `/price ethereum`

## Setup

1. Install the required dependencies:
```bash
pip install python-telegram-bot aiohttp
```

2. Configure your bot token in `config.json`:
```json
{
    "bot_token": "YOUR_BOT_TOKEN"
}
```

3. Run the bot:
```bash
python crypto_price_bot.py
```

## Data Source

Price data is fetched from the CoinGecko API.

## License

MIT License 