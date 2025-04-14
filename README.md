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
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your credentials:
```env
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=@your_channel_name
```

To get your bot token:
1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot using the `/newbot` command
3. Copy the token provided by BotFather

3. Run the bot:
```bash
python crypto_price_bot.py
```

## Security Notes

- Never commit your `.env` file to version control
- If you accidentally expose your bot token, revoke it immediately using [@BotFather](https://t.me/botfather)
- Keep your channel ID private if the channel is private

## Data Source

Price data is fetched from the CoinGecko API.

## License

MIT License 