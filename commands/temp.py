import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import logging
import sqlite3
import os

logger = logging.getLogger('bot')

class TempRoleDB:
    def __init__(self):
        self.db_path = "database/temp_roles.db"
        self.init_db()

    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        os.makedirs("database", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS temp_roles (
                user_id INTEGER,
                role_id INTEGER,
                guild_id INTEGER,
                start_time TIMESTAMP,
                duration TEXT,
                start_message TEXT,
                end_message TEXT,
                PRIMARY KEY (user_id, role_id, guild_id)
            )
        ''')
        conn.commit()
        conn.close()

    def add_temp_role(self, user_id: int, role_id: int, guild_id: int, start_time: datetime, 
                     duration: str, start_message: str, end_message: str):
        """Add a new temporary role assignment"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO temp_roles 
            (user_id, role_id, guild_id, start_time, duration, start_message, end_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, role_id, guild_id, start_time.isoformat(), duration, start_message, end_message))
        conn.commit()
        conn.close()

    def remove_temp_role(self, user_id: int, role_id: int, guild_id: int):
        """Remove a temporary role assignment"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            DELETE FROM temp_roles 
            WHERE user_id = ? AND role_id = ? AND guild_id = ?
        ''', (user_id, role_id, guild_id))
        conn.commit()
        conn.close()

    def get_temp_role(self, user_id: int, guild_id: int):
        """Get active temporary role for a user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT role_id, start_time, duration, start_message, end_message
            FROM temp_roles
            WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))
        result = c.fetchone()
        conn.close()
        return result

    def get_all_active_roles(self):
        """Get all active temporary roles"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM temp_roles')
        results = c.fetchall()
        conn.close()
        return results

class ConfirmView(discord.ui.View):
    def __init__(self, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

class TempRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = TempRoleDB()
        self.active_tasks = {}

    async def send_role_dm(self, member: discord.Member, role: discord.Role, message: str, title: str, color: discord.Color):
        """Helper function to send role-related DMs"""
        try:
            embed = discord.Embed(
                title=title,
                description=message,
                color=color
            )
            embed.add_field(name="Role", value=role.mention, inline=True)
            embed.add_field(name="Server", value=member.guild.name, inline=True)
            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            logger.warning(f"Could not send DM to {member.name} - DMs are closed")
            return False
        except Exception as e:
            logger.error(f"Error sending DM to {member.name}: {str(e)}")
            return False

    def get_remaining_seconds(self, start_time: datetime, duration: str) -> int:
        """Calculate remaining seconds for a temporary role"""
        duration_map = {
            "5m": 300,
            "30m": 1800,
            "1h": 3600,
            "6h": 21600,
            "1d": 86400,
            "7d": 604800
        }
        total_seconds = duration_map[duration]
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        remaining_seconds = total_seconds - elapsed_seconds
        return max(0, int(remaining_seconds))

    async def handle_temp_role(self, member: discord.Member, role: discord.Role, 
                             start_time: datetime, duration: str, 
                             start_message: str, end_message: str):
        """Handle the temporary role assignment and removal"""
        try:
            # Add role
            await member.add_roles(role)
            
            # Send start message
            try:
                embed = discord.Embed(
                    title="Role Assigned",
                    description=start_message,
                    color=role.color
                )
                embed.add_field(name="Role", value=role.mention, inline=True)
                embed.add_field(name="Duration", value=duration, inline=True)
                embed.add_field(name="Server", value=member.guild.name, inline=True)
                await member.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Could not send DM to {member.name} - DMs are closed")
            except Exception as e:
                logger.error(f"Error sending DM to {member.name}: {str(e)}")

            # Calculate remaining time
            remaining_seconds = self.get_remaining_seconds(start_time, duration)
            
            # Wait for remaining time
            await asyncio.sleep(remaining_seconds)

            # Remove role
            await member.remove_roles(role)
            
            # Send end message
            try:
                embed = discord.Embed(
                    title="Role Removed",
                    description=end_message,
                    color=discord.Color.red()
                )
                embed.add_field(name="Role", value=role.mention, inline=True)
                embed.add_field(name="Server", value=member.guild.name, inline=True)
                await member.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Could not send DM to {member.name} - DMs are closed")
            except Exception as e:
                logger.error(f"Error sending DM to {member.name}: {str(e)}")

            # Remove from database
            self.db.remove_temp_role(member.id, role.id, member.guild.id)

        except Exception as e:
            logger.error(f"Error handling temp role for {member.name}: {str(e)}")
            raise

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join events to restore temporary roles"""
        temp_role = self.db.get_temp_role(member.id, member.guild.id)
        if temp_role:
            role_id, start_time, duration, start_message, end_message = temp_role
            role = member.guild.get_role(role_id)
            if role:
                start_time = datetime.fromisoformat(start_time)
                # Start new task for remaining time
                task = asyncio.create_task(
                    self.handle_temp_role(
                        member, role, start_time, duration,
                        start_message, end_message
                    )
                )
                self.active_tasks[(member.id, role_id, member.guild.id)] = task

    @app_commands.command(
        name="temp",
        description="Give a temporary role to a user"
    )
    @app_commands.describe(
        member="The user to give the role to",
        role="The role to give",
        duration="How long to give the role for",
        start_message="Message to send to the user when role is given",
        end_message="Message to send to the user when role is removed"
    )
    @app_commands.choices(duration=[
        app_commands.Choice(name="5 minutes", value="5m"),
        app_commands.Choice(name="30 minutes", value="30m"),
        app_commands.Choice(name="1 hour", value="1h"),
        app_commands.Choice(name="6 hours", value="6h"),
        app_commands.Choice(name="1 day", value="1d"),
        app_commands.Choice(name="7 days", value="7d"),
    ])
    async def temp_role(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        duration: str,
        start_message: str,
        end_message: str
    ):
        # Permission checks
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("I don't have permission to manage roles!", ephemeral=True)
            return

        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message("I can't assign this role because it's higher than or equal to my highest role!", ephemeral=True)
            return

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You don't have permission to manage roles!", ephemeral=True)
            return

        if role.position >= interaction.user.top_role.position:
            await interaction.response.send_message("You can't assign this role because it's higher than or equal to your highest role!", ephemeral=True)
            return

        # Create confirmation embed
        confirm_embed = discord.Embed(
            title="Confirm Temporary Role",
            description="Please confirm the following temporary role assignment:",
            color=role.color
        )
        confirm_embed.add_field(name="User", value=member.mention, inline=True)
        confirm_embed.add_field(name="Role", value=role.mention, inline=True)
        confirm_embed.add_field(name="Duration", value=duration, inline=True)
        confirm_embed.add_field(name="Start Message", value=start_message, inline=False)
        confirm_embed.add_field(name="End Message", value=end_message, inline=False)
        confirm_embed.set_footer(text="Click Confirm to proceed or Cancel to abort")

        # Show confirmation buttons
        view = ConfirmView()
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)

        # Wait for user confirmation
        await view.wait()

        if view.value is None:
            await interaction.followup.send("Operation timed out.", ephemeral=True)
            return
        elif not view.value:
            await interaction.followup.send("Operation cancelled.", ephemeral=True)
            return

        try:
            # Store in database
            start_time = datetime.now()
            self.db.add_temp_role(
                member.id, role.id, member.guild.id,
                start_time, duration, start_message, end_message
            )

            # Start the role management task
            task = asyncio.create_task(
                self.handle_temp_role(
                    member, role, start_time, duration,
                    start_message, end_message
                )
            )
            self.active_tasks[(member.id, role.id, member.guild.id)] = task

            # Send confirmation
            await interaction.followup.send(
                f"✅ Gave {role.mention} to {member.mention} for {duration}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
            logger.error(f"Error in temp role command: {str(e)}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Restore all active temporary roles on bot startup"""
        active_roles = self.db.get_all_active_roles()
        for role_data in active_roles:
            user_id, role_id, guild_id, start_time, duration, start_message, end_message = role_data
            guild = self.bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user_id)
                role = guild.get_role(role_id)
                if member and role:
                    start_time = datetime.fromisoformat(start_time)
                    # Only restore if time hasn't expired
                    if self.get_remaining_seconds(start_time, duration) > 0:
                        task = asyncio.create_task(
                            self.handle_temp_role(
                                member, role, start_time, duration,
                                start_message, end_message
                            )
                        )
                        self.active_tasks[(user_id, role_id, guild_id)] = task

async def setup(bot):
    await bot.add_cog(TempRole(bot)) 