const { MongoClient } = require('mongodb');
require('dotenv').config();

// MongoDB connection URI
const uri = process.env.MONGODB_URI;
const dbName = process.env.DB_NAME || 'discord_bot';
const collectionName = process.env.MEMBERS_COLLECTION || 'members';

// Global client instance
let client = null;
let db = null;
let membersCollection = null;

// Connect to MongoDB
async function connectToDatabase() {
  if (client) return { db, membersCollection };
  
  try {
    console.log('Connecting to MongoDB...');
    client = new MongoClient(uri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      serverSelectionTimeoutMS: 5000,
      maxPoolSize: 10,
      connectTimeoutMS: 10000,
    });
    
    await client.connect();
    console.log('Connected to MongoDB successfully');
    
    // Initialize database and collection
    db = client.db(dbName);
    membersCollection = db.collection(collectionName);
    
    // Create index for faster queries if it doesn't exist
    const indexes = await membersCollection.listIndexes().toArray();
    const hasUserIdIndex = indexes.some(index => 
      index.key && index.key.user_id === 1 && index.unique
    );
    
    if (!hasUserIdIndex) {
      await membersCollection.createIndex({ user_id: 1 }, { unique: true });
      console.log('Created index on user_id field');
    }
    
    return { db, membersCollection };
  } catch (error) {
    console.error('MongoDB connection error:', error);
    client = null;
    throw error;
  }
}

// Close MongoDB connection
async function closeConnection() {
  if (client) {
    await client.close();
    client = null;
    db = null;
    membersCollection = null;
    console.log('MongoDB connection closed');
  }
}

// Get members collection
async function getMembersCollection() {
  if (!membersCollection) {
    await connectToDatabase();
  }
  return membersCollection;
}

module.exports = {
  connectToDatabase,
  closeConnection,
  getMembersCollection,
};