import os
import sys
import logging
import asyncio
import traceback
from dotenv import load_dotenv
import discord
from discord.ext import commands
from database.db_handler import DatabaseHandler
from utils.logger import setup_logger

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set!")

# Setup logging
logger = setup_logger('bot')

# Define intents
intents = discord.Intents.default()
intents.members = True  # Need members intent for tracking
intents.guilds = True
intents.message_content = True  # Add message content intent for commands

# Initialize bot with slash command support
bot = commands.Bot(command_prefix="!", intents=intents)
db = DatabaseHandler()

async def log_to_channel(message):
    """Send logs to Discord channel if configured"""
    if LOG_CHANNEL_ID:
        try:
            channel = bot.get_channel(int(LOG_CHANNEL_ID))
            if channel:
                # Split long messages to avoid Discord's 2000 character limit
                if len(message) > 1900:
                    chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
                    for chunk in chunks:
                        await channel.send(f"```\n{chunk}\n```")
                else:
                    await channel.send(f"```\n{message}\n```")
        except Exception as e:
            logger.error(f"Failed to log to channel: {e}")

@bot.event
async def on_ready():
    """Initialize bot and sync commands when ready"""
    logger.info(f"{bot.user.name} has connected to Discord!")
    
    # Sync app commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        await log_to_channel(f"ERROR: Failed to sync commands: {e}")
    
    # Load all member data on startup
    for guild in bot.guilds:
        message = f"Connected to guild: {guild.name} (id: {guild.id})"
        logger.info(message)
        await log_to_channel(message)
        
        try:
            # Fetch and store all members
            await fetch_all_members(guild)
        except Exception as e:
            error_msg = f"Error processing guild {guild.name}: {str(e)}"
            logger.error(error_msg)
            await log_to_channel(f"ERROR: {error_msg}")

async def fetch_all_members(guild):
    """Fetch and store all members' data"""
    try:
        members_processed = 0
        errors = 0
        for member in guild.members:
            if not member.bot:  # Skip bots
                try:
                    # Get roles (excluding @everyone)
                    roles = [role.id for role in member.roles if role.name != "@everyone"]
                    
                    # Store in database
                    success = await db.update_member(
                        user_id=str(member.id),
                        roles=roles,
                        nickname=member.nick
                    )
                    if success:
                        members_processed += 1
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
                    logger.error(f"Error processing member {member.id}: {str(e)}")
        
        message = f"Stored data for {members_processed} members in {guild.name} ({errors} errors)"
        logger.info(message)
        await log_to_channel(message)
    except Exception as e:
        error_msg = f"Error fetching members: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await log_to_channel(f"ERROR: {error_msg}")

# Load command extensions
async def load_extensions():
    """Load all command and event handlers"""
    try:
        # Import the modules
        from events.member_events import MemberEventsCog
        from commands.all_slash_commands import CommandsCog
        from commands.temp import TempRole
        
        # Add the cogs
        await bot.add_cog(CommandsCog(bot, db))
        await bot.add_cog(MemberEventsCog(bot, db))
        await bot.add_cog(TempRole(bot))
        logger.info("Successfully loaded all extensions")
    except Exception as e:
        error_msg = f"Failed to load extensions: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await log_to_channel(f"ERROR: {error_msg}")
        raise

# Main entry point
async def main():
    """Main entry point for the bot"""
    try:
        # Initialize database connection
        await db.connect()
        
        # Load extensions
        await load_extensions()
        
        # Start the bot
        async with bot:
            await bot.start(TOKEN)
    except Exception as e:
        error_msg = f"Critical error: {str(e)}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        await log_to_channel(f"CRITICAL ERROR: {error_msg}")
    finally:
        # Ensure database connection is closed
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown via keyboard interrupt")
    except Exception as e:
        error_msg = f"Unhandled exception: {str(e)}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        sys.exit(1)