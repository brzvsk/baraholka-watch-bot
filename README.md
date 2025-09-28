# Baraholka Watch Bot

A Telegram bot that monitors yarmarka.ge for specific furniture items and sends notifications when new matching listings are found.

## Features

- 🔍 **Smart Scraping**: Monitors https://yarmarka.ge/goods/c_2438/0/0?sort=new every 30 minutes
- 🏠 **Furniture Focus**: Searches for items containing: "стеллаж", "стелаж", "журнальный", "столик", "зеркало"
- 📱 **Telegram Integration**: Sends rich messages with prices, links, and Telegram chat links
- 🚫 **Duplicate Prevention**: Tracks sent ads to avoid spam
- 🐳 **Docker Ready**: Fully containerized for easy deployment

## Quick Start

### Environment Variables

```bash
BOT_TOKEN=8045994724:AAECxH8TtK_fYiaTXwPv7ACzBf0xRht2AIY
CHAT_ID=4938173866
CHECK_INTERVAL_MINUTES=30
YARMARKA_URL=https://yarmarka.ge/goods/c_2438/0/0?sort=new
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
BOT_TOKEN=8045994724:AAECxH8TtK_fYiaTXwPv7ACzBf0xRht2AIY
CHAT_ID=4938173866
CHECK_INTERVAL_MINUTES=30
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

1. **"No products found"** → Website structure may have changed
2. **"Bot connection failed"** → Check BOT_TOKEN and network
3. **"No Telegram links"** → Product pages may have changed structure

### Debug Mode

```bash
# Enable debug logging
export LOGGING_LEVEL=DEBUG
python main.py --once --dry-run
```

## Development

### Adding Keywords

Edit `src/scraper.py`:
```python
self.keywords = ["стеллаж", "стелаж", "журнальный", "столик", "зеркало", "новое_слово"]
```

### Changing Check Interval

Set environment variable:
```bash
export CHECK_INTERVAL_MINUTES=15  # Check every 15 minutes
```

## License

MIT License - Feel free to adapt for your own marketplace monitoring needs!