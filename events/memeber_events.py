import discord
from discord.ext import commands
import logging
import traceback
import os

logger = logging.getLogger('bot.events')

# Configuration for auto-restore (can be disabled via environment variable)
AUTO_RESTORE = os.getenv('AUTO_RESTORE', 'true').lower() == 'true'

class MemberEventsCog(commands.Cog):
    """Cog for handling member-related events"""
    
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Track member role and nickname changes"""
        if before.bot:  # Skip bots
            return
            
        # Check if roles changed
        roles_changed = before.roles != after.roles
        
        # Check if nickname changed
        nickname_changed = before.nick != after.nick
        
        # Only update database if something changed
        if roles_changed or nickname_changed:
            try:
                # Get all roles except @everyone
                roles = [role.id for role in after.roles if role.name != "@everyone"]
                
                # Store updated data
                await self.db.update_member(
                    user_id=str(after.id),
                    roles=roles,
                    nickname=after.nick
                )
                
                if roles_changed:
                    added_roles = set(after.roles) - set(before.roles)
                    removed_roles = set(before.roles) - set(after.roles)
                    
                    added_role_names = [role.name for role in added_roles if role.name != "@everyone"]
                    removed_role_names = [role.name for role in removed_roles if role.name != "@everyone"]
                    
                    if added_role_names:
                        logger.info(f"User {after.name} ({after.id}) roles added: {', '.join(added_role_names)}")
                    
                    if removed_role_names:
                        logger.info(f"User {after.name} ({after.id}) roles removed: {', '.join(removed_role_names)}")
                
                if nickname_changed:
                    logger.info(f"User {after.name} ({after.id}) nickname changed: '{before.nick}' -> '{after.nick}'")
                
            except Exception as e:
                error_msg = f"Error updating member data: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Keep data when member leaves"""
        if member.bot:  # Skip bots
            return
            
        try:
            # We don't need to do anything here as data is already stored
            # and will be preserved when the member leaves
            logger.info(f"Member left: {member.name} ({member.id}) - Data preserved")
        except Exception as e:
            error_msg = f"Error handling member leave: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Restore roles and nickname when member rejoins"""
        if member.bot:  # Skip bots
            return
            
        # Only attempt auto-restore if enabled
        if not AUTO_RESTORE:
            logger.info(f"Member joined: {member.name} ({member.id}) - Auto-restore disabled")
            return
            
        try:
            # Get stored data
            member_data = await self.db.get_member(str(member.id))
            
            if not member_data:
                logger.info(f"Member joined: {member.name} ({member.id}) - No stored data found")
                return
                
            logger.info(f"Member rejoined: {member.name} ({member.id}) - Attempting to restore data")
            
            # Get bot's highest role for permission checking
            bot_member = member.guild.get_member(self.bot.user.id)
            if not bot_member:
                logger.error(f"Bot member not found in guild {member.guild.id}")
                return
                
            bot_top_role = bot_member.top_role
            
            # Track restore stats
            roles_restored = []
            roles_failed = []
            
            # Restore roles
            for role_id in member_data.get("roles", []):
                role = member.guild.get_role(int(role_id))
                
                # Skip if role doesn't exist
                if not role:
                    roles_failed.append(f"Role {role_id} no longer exists")
                    continue
                
                # Skip if bot can't assign this role
                if role >= bot_top_role:
                    roles_failed.append(f"Role {role.name} is higher than bot's highest role")
                    continue
                
                try:
                    await member.add_roles(role, reason="Automatic role restore on rejoin")
                    roles_restored.append(role.name)
                except discord.Forbidden:
                    roles_failed.append(f"Missing permissions to assign {role.name}")
                except Exception as e:
                    roles_failed.append(f"Error assigning {role.name}: {str(e)}")
            
            # Restore nickname if it exists
            nickname_result = "No nickname to restore"
            stored_nickname = member_data.get("nickname")
            
            if stored_nickname:
                try:
                    await member.edit(nick=stored_nickname, reason="Automatic nickname restore on rejoin")
                    nickname_result = f"Restored nickname: {stored_nickname}"
                except discord.Forbidden:
                    nickname_result = "Missing permissions to set nickname"
                except Exception as e:
                    nickname_result = f"Error setting nickname: {str(e)}"
            
            # Log results
            restored_count = len(roles_restored)
            failed_count = len(roles_failed)
            
            log_msg = (
                f"Member restore for {member.name} ({member.id}): "
                f"Restored {restored_count} roles, {failed_count} failed, {nickname_result}"
            )
            logger.info(log_msg)
            
            # Log to Discord channel if configured
            log_channel_id = os.getenv('LOG_CHANNEL_ID')
            if log_channel_id:
                try:
                    channel = member.guild.get_channel(int(log_channel_id))
                    if channel:
                        embed = discord.Embed(
                            title="Member Rejoined - Data Restore",
                            description=f"User: {member.mention} ({member.id})",
                            color=discord.Color.green()
                        )
                        
                        embed.add_field(
                            name="Nickname",
                            value=nickname_result,
                            inline=False
                        )
                        
                        if roles_restored:
                            embed.add_field(
                                name=f"Roles Restored ({restored_count})",
                                value=", ".join(roles_restored),
                                inline=False
                            )
                        
                        if roles_failed:
                            embed.add_field(
                                name=f"Failed Roles ({failed_count})",
                                value="\n".join(roles_failed),
                                inline=False
                            )
                            
                        await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to log to Discord channel: {e}")
            
        except Exception as e:
            error_msg = f"Error handling member join: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)