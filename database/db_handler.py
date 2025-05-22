import os
import sqlite3
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger('bot.database')

class DatabaseHandler:
    """Handles all database operations for the Discord bot using SQLite"""
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.cursor = None
        self.db_path = 'database/discord_bot.db'
        
    async def connect(self):
        """Connect to SQLite database"""
        try:
            # Ensure database directory exists
            Path('database').mkdir(exist_ok=True)
            
            # Connect to SQLite database
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS members (
                    user_id TEXT PRIMARY KEY,
                    roles TEXT,
                    nickname TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("Connected to SQLite database successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {str(e)}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("SQLite database connection closed")
    
    async def update_member(self, user_id, roles, nickname=None):
        """Update or insert member data"""
        try:
            # Convert roles list to string for storage
            roles_str = ','.join(map(str, roles)) if roles else ''
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO members (user_id, roles, nickname, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, roles_str, nickname))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database operation failed for user_id {user_id}: {str(e)}")
            return False
    
    async def get_member(self, user_id):
        """Get member data from database"""
        try:
            self.cursor.execute('SELECT * FROM members WHERE user_id = ?', (user_id,))
            member_data = self.cursor.fetchone()
            
            if member_data:
                # Convert roles string back to list
                roles = member_data[1].split(',') if member_data[1] else []
                return {
                    'user_id': member_data[0],
                    'roles': roles,
                    'nickname': member_data[2],
                    'last_updated': member_data[3]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get member data for user_id {user_id}: {str(e)}")
            return None
    
    async def delete_member(self, user_id):
        """Delete member data from database"""
        try:
            self.cursor.execute('DELETE FROM members WHERE user_id = ?', (user_id,))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Deleted member data for user_id {user_id}")
                return True
            else:
                logger.warning(f"No data found to delete for user_id {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete member data for user_id {user_id}: {str(e)}")
            return False
    
    async def clear_database(self):
        """Clear entire database - ADMIN ONLY"""
        try:
            self.cursor.execute('DELETE FROM members')
            self.conn.commit()
            count = self.cursor.rowcount
            logger.warning(f"Cleared database, removed {count} records")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear database: {str(e)}")
            return 0
            
    async def get_all_members(self):
        """Get all members from database"""
        try:
            self.cursor.execute('SELECT * FROM members')
            members = self.cursor.fetchall()
            
            return [{
                'user_id': member[0],
                'roles': member[1].split(',') if member[1] else [],
                'nickname': member[2],
                'last_updated': member[3]
            } for member in members]
            
        except Exception as e:
            logger.error(f"Failed to get all members: {str(e)}")
            return []