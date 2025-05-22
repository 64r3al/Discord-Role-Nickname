Discord Role/Nickname Management Bot
A production-ready Discord bot system for tracking and restoring member roles and nicknames across rejoins. The system consists of a primary Python Discord bot and a secondary JavaScript API service, both using MongoDB for data storage.

Features
Core Functionality
Tracks member roles and nicknames automatically
Preserves roles and nicknames when members leave
Restores roles and nicknames when members rejoin
Provides slash commands for data management
Secure API interface for integration with other systems
Technical Features
Role hierarchy validation and permission checks
Comprehensive logging system
Security features for bot and API
Error handling and graceful retries
Scalable configuration via environment variables
System Architecture
Python Discord Bot
Built with discord.py using application commands
Handles all Discord event listening and interactions
Provides slash commands for data management
Includes comprehensive logging and error handling
JavaScript API Service
Built with Express.js
Provides RESTful API for the same MongoDB database
Enables integration with external systems
Includes API key authentication and validation
MongoDB Database
Stores user IDs, roles, and nicknames
Enables persistence across user leaves/joins
Shared between both components of the system
Setup Instructions
Prerequisites
Python 3.8+
Node.js 16+
MongoDB 4.4+
Discord Bot Token (with proper intents enabled)
Discord Bot Setup
Create a Discord application at the Discord Developer Portal
Enable the "Server Members Intent" under the Bot settings
Generate an invite URL with the following permissions:
Manage Roles
Manage Nicknames
View Channels
Send Messages
Environment Setup
Clone the repository
Navigate to the bot directory
Copy .env.sample to .env
Fill in the required environment variables
Install dependencies:
bash
