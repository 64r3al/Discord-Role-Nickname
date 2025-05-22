import discord
from discord import app_commands
import logging
import os

logger = logging.getLogger('bot.permissions')

# Get admin role ID from environment variable, if available
ADMIN_ROLE_ID = os.getenv('ADMIN_ROLE_ID')

async def is_admin(interaction: discord.Interaction) -> bool:
    """Check if user has admin permissions
    
    Checks for either:
    1. Server administrator permission
    2. Specific admin role ID (if configured in .env)
    3. Server owner status
    """
    user = interaction.user
    
    # Check if user is server owner
    if interaction.guild.owner_id == user.id:
        return True
    
    # Check if user has administrator permission
    if user.guild_permissions.administrator:
        return True
    
    # Check for specific admin role if configured
    if ADMIN_ROLE_ID:
        admin_role = discord.utils.get(interaction.guild.roles, id=int(ADMIN_ROLE_ID))
        if admin_role and admin_role in user.roles:
            return True
    
    logger.warning(f"User {user.name} ({user.id}) attempted to use admin command without permission")
    return False

async def has_manage_roles(interaction: discord.Interaction) -> bool:
    """Check if user has manage roles permission
    
    Checks for either:
    1. Manage roles permission
    2. Admin status (via is_admin check)
    """
    user = interaction.user
    
    # First check if user is admin
    if await is_admin(interaction):
        return True
    
    # Check if user has manage roles permission
    if user.guild_permissions.manage_roles:
        return True
    
    logger.warning(f"User {user.name} ({user.id}) attempted to use manage roles command without permission")
    return False