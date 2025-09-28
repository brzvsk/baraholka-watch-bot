# Baraholka Watch Bot

A Telegram bot that monitors yarmarka.ge for specific furniture items and sends notifications when new matching listings are found.

## Features

- 🔍 **Smart Scraping**: Monitors yarmarka.ge listings every 30 minutes (configurable)
- 🔎 **Configurable Search**: Customizable keywords via environment variables  
- 🏠 **Furniture Focus**: Default search for стеллаж, стелаж, журнальный, столик, зеркало
- 📱 **Telegram Integration**: Sends rich messages with prices, links, and Telegram chat links
- 🚫 **Duplicate Prevention**: Tracks sent ads to avoid spam
- 🔒 **Secure**: All secrets stored in environment variables
- 🐳 **Docker Ready**: Fully containerized for easy deployment

## Quick Start

### Environment Variables

```bash
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id  # Use negative ID for groups: -1234567890

# Scraping Configuration
CHECK_INTERVAL_MINUTES=30
YARMARKA_URL=https://yarmarka.ge/goods/c_2438/0/0?sort=new
SEARCH_KEYWORDS=стеллаж,стелаж,журнальный,столик,зеркало
```

### Local Testing

1. **Setup Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Test Connection**:
   ```bash
   python main.py --test-connection
   ```

3. **Dry Run** (no actual messages):
   ```bash
   python main.py --once --dry-run
   ```

4. **Single Run**:
   ```bash
   python main.py --once
   ```

5. **Start Monitoring**:
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build & Run**:
   ```bash
   docker-compose up -d
   ```

2. **View Logs**:
   ```bash
   docker-compose logs -f
   ```

### Coolify Deployment

1. **Repository**: https://github.com/brzvsk/baraholka-watch-bot
2. **Project**: j4kogg4skkgwsg04cwo8wccg
3. **Environment**: wggswo8kwkg4004owkgg00k4
4. **Container**: Uses Dockerfile for automatic building

#### Environment Variables to Set in Coolify:
```
# Required
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id

# Optional (with defaults)
CHECK_INTERVAL_MINUTES=30
SEARCH_KEYWORDS=стеллаж,стелаж,журнальный,столик,зеркало
YARMARKA_URL=https://yarmarka.ge/goods/c_2438/0/0?sort=new
```

#### Coolify Configuration:
- **Build Type**: Dockerfile
- **Port**: Not applicable (background service)
- **Restart Policy**: Always
- **Health Check**: Built-in Telegram API connection test

## Bot Commands

### CLI Arguments

- `--dry-run`: Run without sending actual messages
- `--once`: Run once and exit (for testing)
- `--test-connection`: Test Telegram bot connection
- `--reset-state`: Clear all tracking data
- `--stats`: Show statistics

### Examples

```bash
# Test everything without sending messages
python main.py --once --dry-run

# Check current statistics
python main.py --stats

# Reset tracking (will re-send old ads)
python main.py --reset-state
```

## Architecture

```
main.py                 # Application orchestrator
├── src/scraper.py      # Web scraping logic
├── src/telegram_bot.py # Telegram notifications
└── src/state_manager.py # Duplicate detection
```

### Data Flow

1. **Scrape** → Fetch listings from yarmarka.ge
2. **Filter** → Match keywords in titles
3. **Extract** → Get Telegram links from product pages
4. **Dedupe** → Check against sent_ads.json
5. **Notify** → Send formatted Telegram messages

## Monitoring

- **Logs**: Available in `bot.log` and Docker logs
- **Health Check**: Telegram API connectivity test
- **State File**: `sent_ads.json` tracks sent notifications
- **Cleanup**: Automatically removes entries older than 7 days

## Troubleshooting

### Common Issues

1. **"Chat not found"** → 
   - For groups: Use negative chat ID (e.g., `-1234567890`)
   - For private chats: Use positive chat ID (e.g., `1234567890`)
   - Add bot to the target chat/group first
2. **"No products found"** → Website structure may have changed
3. **"Bot connection failed"** → Check BOT_TOKEN and network
4. **"No Telegram links"** → Product pages may have changed structure

### Debug Mode

```bash
# Enable debug logging
export LOGGING_LEVEL=DEBUG
python main.py --once --dry-run
```

## Configuration

### Search Keywords

Customize what items to search for by setting the `SEARCH_KEYWORDS` environment variable:

```bash
# Default furniture keywords
SEARCH_KEYWORDS=стеллаж,стелаж,журнальный,столик,зеркало

# Add electronics keywords
SEARCH_KEYWORDS=iPhone,Samsung,ноутбук,компьютер

# Mix categories
SEARCH_KEYWORDS=стеллаж,iPhone,велосипед
```

### Check Interval

Change how often the bot checks for new items:

```bash
CHECK_INTERVAL_MINUTES=15  # Check every 15 minutes
CHECK_INTERVAL_MINUTES=60  # Check every hour
```

### Target URL

Monitor different marketplace categories:

```bash
# Default furniture category
YARMARKA_URL=https://yarmarka.ge/goods/c_2438/0/0?sort=new

# Electronics category (example)
YARMARKA_URL=https://yarmarka.ge/goods/c_1234/0/0?sort=new
```

## Development

## License

MIT License - Feel free to adapt for your own marketplace monitoring needs!