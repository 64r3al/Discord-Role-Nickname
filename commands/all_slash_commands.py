import discord
from discord import app_commands
from discord.ext import commands
import logging
import traceback
from utils.permission_checks import is_admin, has_manage_roles

logger = logging.getLogger('bot.commands')

class CommandsCog(commands.Cog):
    """Cog containing all slash commands for the bot"""
    
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        
    async def log_command(self, interaction, command_name, success=True, details=None):
        """Log command usage to both logger and Discord channel if configured"""
        user = interaction.user
        guild = interaction.guild
        
        log_message = (
            f"Command: /{command_name} | "
            f"User: {user.name}#{user.discriminator} ({user.id}) | "
            f"Guild: {guild.name} ({guild.id}) | "
            f"Status: {'Success' if success else 'Failed'}"
        )
        
        if details:
            log_message += f" | Details: {details}"
        
        if success:
            logger.info(log_message)
        else:
            logger.warning(log_message)
            
        # Log to Discord channel if configured
        log_channel_id = discord.utils.get(guild.text_channels, name="bot-logs")
        if log_channel_id:
            try:
                await log_channel_id.send(f"```\n{log_message}\n```")
            except Exception as e:
                logger.error(f"Failed to log to Discord channel: {e}")
    
    @app_commands.command(
        name="fetchall",
        description="Fetch and store all current member data"
    )
    @app_commands.check(is_admin)
    async def fetchall(self, interaction: discord.Interaction):
        """Fetch and store data for all members in the guild"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            member_count = 0
            
            for member in guild.members:
                if not member.bot:  # Skip bots
                    # Get roles (excluding @everyone)
                    roles = [role.id for role in member.roles if role.name != "@everyone"]
                    
                    # Store in database
                    await self.db.update_member(
                        user_id=str(member.id),
                        roles=roles,
                        nickname=member.nick
                    )
                    member_count += 1
            
            await interaction.followup.send(f"✅ Successfully stored data for {member_count} members!", ephemeral=True)
            await self.log_command(interaction, "fetchall", True, f"Processed {member_count} members")
            
        except Exception as e:
            error_msg = f"Error fetching members: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            await self.log_command(interaction, "fetchall", False, str(e))
    
    @app_commands.command(
        name="viewdata",
        description="View stored roles and nickname for a user"
    )
    @app_commands.describe(
        user="The user to view data for"
    )
    @app_commands.check(has_manage_roles)
    async def viewdata(self, interaction: discord.Interaction, user: discord.User):
        """View stored data for a specific user"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get data from database
            member_data = await self.db.get_member(str(user.id))
            
            if not member_data:
                await interaction.followup.send(f"❌ No data found for {user.mention}", ephemeral=True)
                await self.log_command(interaction, "viewdata", False, f"No data for user {user.id}")
                return
            
            # Format roles for display
            stored_roles = []
            for role_id in member_data.get("roles", []):
                role = interaction.guild.get_role(int(role_id))
                role_name = role.name if role else f"Unknown Role ({role_id})"
                stored_roles.append(f"- {role_name} ({role_id})")
            
            roles_text = "\n".join(stored_roles) if stored_roles else "None"
            nickname = member_data.get("nickname") or "None"
            
            # Create embed for better display
            embed = discord.Embed(
                title=f"Stored Data for {user.name}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Nickname", value=nickname, inline=False)
            embed.add_field(name="Stored Roles", value=roles_text, inline=False)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.log_command(interaction, "viewdata", True, f"User {user.id}")
            
        except Exception as e:
            error_msg = f"Error viewing data: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            await self.log_command(interaction, "viewdata", False, str(e))
    
    @app_commands.command(
        name="restore",
        description="Restore roles and nickname for a user"
    )
    @app_commands.describe(
        user="The user to restore data for"
    )
    @app_commands.check(has_manage_roles)
    async def restore(self, interaction: discord.Interaction, user: discord.User):
        """Restore roles and nickname for a specific user"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is in the guild
            member = interaction.guild.get_member(user.id)
            if not member:
                await interaction.followup.send(f"❌ {user.mention} is not in this server", ephemeral=True)
                await self.log_command(interaction, "restore", False, f"User {user.id} not in guild")
                return
            
            # Get data from database
            member_data = await self.db.get_member(str(user.id))
            
            if not member_data:
                await interaction.followup.send(f"❌ No data found for {user.mention}", ephemeral=True)
                await self.log_command(interaction, "restore", False, f"No data for user {user.id}")
                return
            
            # Get bot's highest role for permission checking
            bot_member = interaction.guild.get_member(self.bot.user.id)
            bot_top_role = bot_member.top_role
            
            # Get the user's current roles
            current_roles = set(role.id for role in member.roles if role.name != "@everyone")
            
            # Get the roles to be restored
            roles_to_restore = set(int(role_id) for role_id in member_data.get("roles", []))
            
            # Calculate roles to add and remove
            roles_to_add = roles_to_restore - current_roles
            
            # Store stats for reporting
            added_roles = []
            failed_roles = []
            
            # Add roles
            for role_id in roles_to_add:
                role = interaction.guild.get_role(role_id)
                if not role:
                    failed_roles.append(f"Role {role_id} does not exist")
                    continue
                    
                # Check if bot can manage this role
                if role >= bot_top_role:
                    failed_roles.append(f"{role.name} - higher than bot's role")
                    continue
                    
                try:
                    await member.add_roles(role, reason="Automatic role restore")
                    added_roles.append(role.name)
                except discord.Forbidden:
                    failed_roles.append(f"{role.name} - missing permissions")
                except Exception as e:
                    failed_roles.append(f"{role.name} - {str(e)}")
            
            # Restore nickname if it exists
            nickname_result = "No change"
            if member_data.get("nickname") and member_data["nickname"] != member.nick:
                try:
                    await member.edit(nick=member_data["nickname"], reason="Automatic nickname restore")
                    nickname_result = f"Changed to {member_data['nickname']}"
                except discord.Forbidden:
                    nickname_result = "Failed - missing permissions"
                except Exception as e:
                    nickname_result = f"Failed - {str(e)}"
            
            # Create response
            embed = discord.Embed(
                title=f"Restore Results for {user.name}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Nickname",
                value=nickname_result,
                inline=False
            )
            
            embed.add_field(
                name="Roles Added",
                value="\n".join(added_roles) or "None",
                inline=False
            )
            
            if failed_roles:
                embed.add_field(
                    name="Failed Roles",
                    value="\n".join(failed_roles),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Log the command
            details = f"User {user.id}: Added {len(added_roles)} roles, {len(failed_roles)} failed"
            await self.log_command(interaction, "restore", True, details)
            
        except Exception as e:
            error_msg = f"Error restoring data: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            await self.log_command(interaction, "restore", False, str(e))
    
    @app_commands.command(
        name="cleardata",
        description="Delete stored data for a specific user"
    )
    @app_commands.describe(
        user="The user to delete data for"
    )
    @app_commands.check(is_admin)
    async def cleardata(self, interaction: discord.Interaction, user: discord.User):
        """Delete stored data for a specific user"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Delete from database
            success = await self.db.delete_member(str(user.id))
            
            if success:
                await interaction.followup.send(f"✅ Successfully deleted data for {user.mention}", ephemeral=True)
                await self.log_command(interaction, "cleardata", True, f"Deleted data for user {user.id}")
            else:
                await interaction.followup.send(f"❌ No data found for {user.mention}", ephemeral=True)
                await self.log_command(interaction, "cleardata", False, f"No data for user {user.id}")
            
        except Exception as e:
            error_msg = f"Error clearing data: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            await self.log_command(interaction, "cleardata", False, str(e))
    
    @app_commands.command(
        name="cleardb",
        description="Delete all stored data (ADMIN ONLY)"
    )
    @app_commands.check(is_admin)
    async def cleardb(self, interaction: discord.Interaction):
        """Clear the entire database - ADMIN ONLY"""
        await interaction.response.defer(ephemeral=True)
        
        # Confirmation button to prevent accidental deletions
        confirm_view = ConfirmView()
        await interaction.followup.send(
            "⚠️ **WARNING** ⚠️\nThis will delete ALL stored member data. This action cannot be undone.\n"
            "Are you sure you want to continue?",
            view=confirm_view,
            ephemeral=True
        )
        
        # Wait for button interaction
        await confirm_view.wait()
        
        if confirm_view.value is True:
            try:
                # Clear database
                deleted_count = await self.db.clear_database()
                
                await interaction.followup.send(
                    f"✅ Database cleared successfully. Deleted {deleted_count} records.",
                    ephemeral=True
                )
                await self.log_command(interaction, "cleardb", True, f"Deleted {deleted_count} records")
                
            except Exception as e:
                error_msg = f"Error clearing database: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
                await self.log_command(interaction, "cleardb", False, str(e))
        else:
            await interaction.followup.send("Operation cancelled.", ephemeral=True)
    
    # Error handling for command checks
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.CheckFailure):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
        else:
            logger.error(f"Command error: {str(error)}\n{traceback.format_exc()}")
            
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"❌ An error occurred: {str(error)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ An error occurred: {str(error)}",
                    ephemeral=True
                )


# Confirmation view for dangerous operations
class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.value = None
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.edit_message(content="Processing...", view=None)
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.edit_message(content="Operation cancelled.", view=None)
        self.stop()