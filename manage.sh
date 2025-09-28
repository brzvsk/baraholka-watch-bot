#!/bin/bash
# Baraholka Watch Bot Management Script

case "$1" in
    start)
        echo "Starting Baraholka Watch Bot..."
        docker compose up -d
        ;;
    stop)
        echo "Stopping Baraholka Watch Bot..."
        docker compose down
        ;;
    restart)
        echo "Restarting Baraholka Watch Bot..."
        docker compose down
        docker compose up -d
        ;;
    logs)
        echo "Showing bot logs (Ctrl+C to exit)..."
        docker compose logs -f
        ;;
    status)
        echo "Bot status:"
        docker compose ps
        ;;
    update)
        echo "Updating bot from GitHub..."
        git pull
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the bot"
        echo "  stop    - Stop the bot"
        echo "  restart - Restart the bot"
        echo "  logs    - Show live logs"
        echo "  status  - Show bot status"
        echo "  update  - Pull latest code and rebuild"
        exit 1
        ;;
esac
