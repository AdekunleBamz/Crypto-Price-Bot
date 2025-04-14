import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from datetime import datetime
import aiohttp
import json
import os
import logging
import sys
from contextlib import suppress
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
CACHE_PATH = os.path.join(SCRIPT_DIR, 'cache.json')

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("No bot token found. Please set BOT_TOKEN in .env file")
    sys.exit(1)

CHANNEL_ID = os.getenv('CHANNEL_ID')
if not CHANNEL_ID:
    logger.error("No channel ID found. Please set CHANNEL_ID in .env file")
    sys.exit(1)

UPDATE_INTERVAL = 1800  # 30 minutes
COINGECKO_API = 'https://api.coingecko.com/api/v3'

# Global variables
coin_cache = {}
should_stop = False

async def load_coin_list():
    """Load and cache the complete coin list from CoinGecko"""
    if not coin_cache:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{COINGECKO_API}/coins/list") as response:
                    if response.status == 200:
                        coins = await response.json()
                        for coin in coins:
                            coin_cache[coin['symbol'].lower()] = {
                                'id': coin['id'],
                                'name': coin['name']
                            }
                        logger.info(f"Loaded {len(coins)} coins into cache")
                        with open(CACHE_PATH, 'w') as f:
                            json.dump(coin_cache, f)
            except Exception as e:
                logger.error(f"Error loading coin list: {e}")
                if os.path.exists(CACHE_PATH):
                    with open(CACHE_PATH, 'r') as f:
                        coin_cache.update(json.load(f))

async def get_crypto_price(coin_id: str):
    """Get detailed price data for a specific cryptocurrency"""
    async with aiohttp.ClientSession() as session:
        try:
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            async with session.get(f"{COINGECKO_API}/simple/price", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        return data.get(coin_id)
                    else:
                        logger.error(f"Coin {coin_id} not found in response data")
                        return None
                elif response.status == 429:  # Rate limit
                    logger.error(f"Rate limit hit for {coin_id}. Waiting before retry...")
                    await asyncio.sleep(60)  # Wait for 60 seconds before next request
                    return None
                else:
                    logger.error(f"Error fetching {coin_id}: Status {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching price for {coin_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {coin_id}: {e}")
            return None

async def format_price_message(coin_id: str, coin_name: str, data: dict) -> str:
    """Format a detailed price message for a cryptocurrency"""
    if not data:
        return f"⚠️ Could not fetch price for {coin_name}"

    price = data.get('usd', 0)
    change = data.get('usd_24h_change', 0)
    volume = data.get('usd_24h_vol', 0)
    market_cap = data.get('usd_market_cap', 0)
    
    change_emoji = "🟢" if change >= 0 else "🔴"
    
    message = f"💎 {coin_name.upper()} ({coin_id.upper()})\n"
    message += f"💵 ${price:,.4f}\n"
    message += f"📊 24h: {change_emoji} {change:.2f}%\n"
    message += f"📈 Vol: ${volume:,.0f}\n"
    message += f"💰 MCap: ${market_cap:,.0f}"
    
    return message

async def send_channel_update():
    """Send scheduled update to channel with major crypto prices"""
    try:
        # Ensure coin list is loaded
        if not coin_cache:
            await load_coin_list()

        major_coins = [
            'bitcoin', 'ethereum', 'solana', 'cosmos-hub', 'aptos',
            'sui', 'arbitrum', 'optimism', 'matic-network'
        ]
        messages = []
        
        for coin_id in major_coins:
            logger.info(f"Fetching price data for {coin_id}")
            data = await get_crypto_price(coin_id)
            if data:
                coin_name = next((k for k, v in coin_cache.items() if v['id'] == coin_id), coin_id)
                message = await format_price_message(coin_id, coin_name, data)
                messages.append(message)
                logger.info(f"Successfully fetched price for {coin_id}")
            else:
                logger.error(f"Failed to fetch price data for {coin_id}")
        
        if messages:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
            final_message = "🚨 Crypto Price Update\n\n" + "\n\n".join(messages)
            final_message += f"\n\n⏰ {timestamp}\n🔗 @bamzz_cryptoalpha"
            
            async with Bot(token=BOT_TOKEN) as bot:
                await bot.send_message(chat_id=CHANNEL_ID, text=final_message)
            logger.info("Channel update sent successfully")
        else:
            logger.error("No price data was fetched for any coins")
    except Exception as e:
        logger.error(f"Error sending channel update: {e}")

async def search_crypto(query: str) -> list:
    """Search for cryptocurrencies matching the query"""
    if not coin_cache:
        await load_coin_list()
    
    query = query.lower()
    matches = []
    
    for symbol, data in coin_cache.items():
        if query in symbol.lower() or query in data['name'].lower():
            matches.append({
                'symbol': symbol,
                'name': data['name'],
                'id': data['id']
            })
            if len(matches) >= 5:
                break
    
    return matches

async def handle_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /p command to search for crypto prices"""
    try:
        if not update.message or not update.message.text:
            return

        query = update.message.text.split()
        if len(query) < 2:
            await update.message.reply_text(
                "Please provide a cryptocurrency symbol or name.\n"
                "Example: /p btc or /p bitcoin"
            )
            return

        search_query = ' '.join(query[1:])
        matches = await search_crypto(search_query)

        if not matches:
            await update.message.reply_text(
                f"❌ No cryptocurrency found matching '{search_query}'\n"
                "Try using the symbol (e.g., btc) or name (e.g., bitcoin)"
            )
            return

        if len(matches) == 1:
            coin = matches[0]
            price_data = await get_crypto_price(coin['id'])
            message = await format_price_message(coin['symbol'], coin['name'], price_data)
            await update.message.reply_text(message)
        else:
            keyboard = []
            for coin in matches:
                button = InlineKeyboardButton(
                    f"{coin['name']} ({coin['symbol'].upper()})",
                    callback_data=f"price_{coin['id']}"
                )
                keyboard.append([button])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Multiple matches found. Select one:",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error in price command: {e}")
        await update.message.reply_text("❌ Error fetching price data")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    try:
        query = update.callback_query
        await query.answer()

        if query.data.startswith('price_'):
            coin_id = query.data.split('_')[1]
            coin_data = next((data for data in coin_cache.values() if data['id'] == coin_id), None)
            
            if coin_data:
                price_data = await get_crypto_price(coin_id)
                message = await format_price_message(coin_id, coin_data['name'], price_data)
                await query.edit_message_text(text=message)
    except Exception as e:
        logger.error(f"Error in callback: {e}")

def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Exception while handling an update: {context.error}")

if __name__ == '__main__':
    try:
        # Initialize bot
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("p", handle_price_command))
        application.add_handler(CommandHandler("price", handle_price_command))
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_error_handler(error_handler)
        
        # Load coin list before starting
        application.job_queue.run_once(lambda _: asyncio.create_task(load_coin_list()), when=0)
        
        # Schedule regular updates
        application.job_queue.run_repeating(
            lambda _: asyncio.create_task(send_channel_update()),
            interval=UPDATE_INTERVAL,
            first=10  # Start first update after 10 seconds
        )
        
        # Start the bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}") 