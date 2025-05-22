import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_CONFIG = {
    # Required settings
    "token": os.getenv("DISCORD_TOKEN"),
    
    # Database settings
    "db_path": os.getenv("DB_PATH", "database/discord_bot.db"),
    
    # Feature flags
    "auto_restore": os.getenv("AUTO_RESTORE", "true").lower() == "true",
    
    # Permissions
    "admin_role_id": os.getenv("ADMIN_ROLE_ID"),
    
    # Logging
    "log_channel_id": os.getenv("LOG_CHANNEL_ID"),
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    
    # Bot behavior
    "command_prefix": os.getenv("COMMAND_PREFIX", "!"),
}

# Validate required configuration
def validate_config():
    """Validate that required configuration is present"""
    required_vars = ["token"]
    missing_vars = [var for var in required_vars if not BOT_CONFIG.get(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please check your .env file or environment variables."
        )

# Call validation on import
validate_config()