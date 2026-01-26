import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from notion_client import Client

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# Initialize Notion client
notion = Client(auth=NOTION_TOKEN)


def parse_message(text: str) -> dict | None:
    """Parse message in format: Title | Category | URL"""
    parts = text.split("|")

    if len(parts) != 3:
        return None

    title = parts[0].strip()
    category = parts[1].strip()
    content = parts[2].strip()

    if not title or not category or not content:
        return None

    return {
        "title": title,
        "category": category,
        "content": content
    }


def save_to_notion(title: str, category: str, content: str) -> bool:
    """Save entry to Notion database"""
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Category": {
                    "select": {
                        "name": category
                    }
                },
                "Content": {
                    "rich_text": [
                        {
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")
        return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    text = update.message.text

    # Parse the message
    parsed = parse_message(text)

    if not parsed:
        await update.message.reply_text(
            "❌ Invalid format. Please use:\n"
            "Title | Category | URL\n\n"
            "Example: 如何用好编程 | video coding | https://twitter.com/example"
        )
        return

    # Save to Notion
    success = save_to_notion(
        parsed["title"],
        parsed["category"],
        parsed["content"]
    )

    if success:
        await update.message.reply_text(
            f"✅ Saved to Notion:\n"
            f"Title: {parsed['title']}\n"
            f"Category: {parsed['category']}"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to save to Notion. Please try again later."
        )


def main() -> None:
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    if not NOTION_TOKEN:
        logger.error("NOTION_TOKEN not set")
        return

    if not NOTION_DATABASE_ID:
        logger.error("NOTION_DATABASE_ID not set")
        return

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Bot started")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
