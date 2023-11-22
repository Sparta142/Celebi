import logging
import os

import discord.utils

from celebi.client import client

# Set up logging before doing anything else
logger = logging.getLogger(__name__)
discord.utils.setup_logging()

# Load environment variables from .env if python-dotenv is installed
try:
    import dotenv
except (ImportError, ModuleNotFoundError):
    logger.warning('Failed to import python-dotenv module', exc_info=True)
else:
    dotenv.load_dotenv(verbose=True)

# Start the bot (don't set up logging twice)
token = os.environ['DISCORD_BOT_TOKEN']
client.run(token, log_handler=None)
