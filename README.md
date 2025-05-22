# Discord Role/Nickname Management Bot

A powerful Discord bot system designed to track and restore member roles and nicknames across server rejoins. Built with Python and featuring a modern, user-friendly interface.

## 🌟 Features

### Core Functionality
- 🔄 Automatic role and nickname tracking
- 💾 Persistent storage of member data
- 🔙 Automatic role restoration on rejoin
- 🛡️ Role hierarchy validation
- 📝 Comprehensive logging system

### Security Features
- 🔐 Secure API authentication
- 🛡️ Permission validation
- 🔒 Role hierarchy checks
- 📊 Audit logging

## 🚀 Quick Start

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   - Copy `.env.sample` to `.env`
   - Fill in your Discord bot token and other settings

4. **Start the Bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Required Environment Variables
```env
DISCORD_TOKEN=your_discord_bot_token_here
LOG_CHANNEL_ID=your_log_channel_id_here
COMMAND_PREFIX=!
AUTO_RESTORE=true
ADMIN_ROLE_ID=your_admin_role_id_here
LOG_LEVEL=INFO
```

### Bot Permissions
The bot requires the following permissions:
- Manage Roles
- Manage Nicknames
- View Channels
- Send Messages
- Read Message History

## 📋 Commands

### User Commands
- `/help` - Display help menu
- `/roles` - View your current roles
- `/nickname` - View your current nickname

### Admin Commands
- `/restore` - Manually restore roles for a user
- `/track` - Enable/disable role tracking for a user
- `/logs` - View recent role changes

## 🛠️ Technical Details

### Requirements
- Python 3.8+
- discord.py
- MongoDB
- Other dependencies listed in requirements.txt

### Database Structure
The bot uses MongoDB to store:
- User IDs
- Role IDs
- Nicknames
- Timestamps
- Audit logs

## 📝 Logging

The bot includes comprehensive logging:
- Role changes
- Nickname changes
- Command usage
- Error tracking
- Audit logs

## 🔧 Troubleshooting

### Common Issues
1. **Bot not responding**
   - Check if the bot is online
   - Verify token is correct
   - Check permissions

2. **Roles not restoring**
   - Verify bot has proper permissions
   - Check role hierarchy
   - Ensure user is being tracked

### Support
For additional support:
- Join our [Discord Server](https://discord.gg/your-server)
- Open an issue on GitHub
- Contact the developer

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Developer

Created by IVX
- [Buy me a coffee](https://guns.lol/ivx.1x)
- [Discord](https://discord.gg/your-server)

---
Made with ❤️ by IVX 