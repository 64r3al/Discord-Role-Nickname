import discord
from discord.ext import commands
import logging
import traceback

logger = logging.getLogger('bot.events')

class MemberEventsCog(commands.Cog):
    """Handle member-related events"""
    
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle when a member joins the server"""
        if member.bot:
            return
            
        try:
            # Get saved member data
            member_data = await self.db.get_member(str(member.id))
            
            if member_data:
                # Get bot's highest role for permission checking
                bot_member = member.guild.get_member(self.bot.user.id)
                bot_top_role = bot_member.top_role
                
                # Get roles to restore
                roles_to_restore = []
                failed_roles = []
                
                for role_id in member_data.get('roles', []):
                    role = member.guild.get_role(int(role_id))
                    if role:
                        # Check if bot can manage this role
                        if role < bot_top_role:
                            roles_to_restore.append(role)
                        else:
                            failed_roles.append(f"{role.name} - higher than bot's role")
                    else:
                        failed_roles.append(f"Role {role_id} no longer exists")
                
                # Add roles
                if roles_to_restore:
                    try:
                        await member.add_roles(*roles_to_restore, reason="Automatic role restoration")
                        logger.info(f"Restored {len(roles_to_restore)} roles to {member.name} ({member.id})")
                    except discord.Forbidden:
                        logger.error(f"Missing permissions to restore roles for {member.name} ({member.id})")
                    except Exception as e:
                        logger.error(f"Error restoring roles for {member.name} ({member.id}): {str(e)}")
                
                # Restore nickname if it exists
                if member_data.get('nickname'):
                    try:
                        await member.edit(nick=member_data['nickname'], reason="Automatic nickname restoration")
                        logger.info(f"Restored nickname for {member.name} ({member.id})")
                    except discord.Forbidden:
                        logger.error(f"Missing permissions to restore nickname for {member.name} ({member.id})")
                    except Exception as e:
                        logger.error(f"Error restoring nickname for {member.name} ({member.id}): {str(e)}")
                
                # Log any failed roles
                if failed_roles:
                    logger.warning(f"Failed to restore some roles for {member.name} ({member.id}): {', '.join(failed_roles)}")
            
            # Store current member data
            roles = [role.id for role in member.roles if role.name != "@everyone"]
            await self.db.update_member(
                user_id=str(member.id),
                roles=roles,
                nickname=member.nick
            )
            logger.info(f"Stored data for member: {member.name} ({member.id})")
            
        except Exception as e:
            logger.error(f"Error handling member join for {member.id}: {str(e)}\n{traceback.format_exc()}")
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Handle when a member's roles or nickname changes"""
        if before.bot:
            return
            
        try:
            # Get roles (excluding @everyone)
            roles = [role.id for role in after.roles if role.name != "@everyone"]
            
            # Update member data if roles or nickname changed
            if roles != [role.id for role in before.roles if role.name != "@everyone"] or before.nick != after.nick:
                await self.db.update_member(
                    user_id=str(after.id),
                    roles=roles,
                    nickname=after.nick
                )
                logger.info(f"Updated data for member: {after.name} ({after.id})")
        except Exception as e:
            logger.error(f"Error handling member update for {after.id}: {str(e)}\n{traceback.format_exc()}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle when a member leaves the server"""
        if member.bot:
            return
            
        try:
            # Store member data before they leave
            roles = [role.id for role in member.roles if role.name != "@everyone"]
            await self.db.update_member(
                user_id=str(member.id),
                roles=roles,
                nickname=member.nick
            )
            logger.info(f"Stored data for leaving member: {member.name} ({member.id})")
        except Exception as e:
            logger.error(f"Error handling member remove for {member.id}: {str(e)}\n{traceback.format_exc()}") 