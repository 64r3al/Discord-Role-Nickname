{
    "name": "discord-bot-api",
    "version": "1.0.0",
    "description": "API service for Discord bot database",
    "main": "server.js",
    "scripts": {
      "start": "node server.js",
      "dev": "nodemon server.js",
      "test": "jest"
    },
    "dependencies": {
      "cors": "^2.8.5",
      "dotenv": "^16.3.1",
      "express": "^4.18.2",
      "express-rate-limit": "^7.1.1",
      "helmet": "^7.0.0",
      "mongodb": "^6.1.0",
      "morgan": "^1.10.0"
    },
    "devDependencies": {
      "jest": "^29.7.0",
      "nodemon": "^3.0.1",
      "supertest": "^6.3.3"
    },
    "engines": {
      "node": ">=16.0.0"
    }
  }