const express = require('express');
const { getMembersCollection } = require('../db/mongo');
const { validateUserData, isAdminUser } = require('../middleware/validators');

const router = express.Router();

/**
 * GET /api/users
 * Get all users
 * Admin only
 */
router.get('/', isAdminUser, async (req, res, next) => {
  try {
    const collection = await getMembersCollection();
    const users = await collection.find({}).toArray();
    
    res.status(200).json({
      success: true,
      count: users.length,
      data: users
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/users/:id
 * Get user by ID
 */
router.get('/:id', async (req, res, next) => {
  try {
    const userId = req.params.id;
    
    // Basic validation
    if (!userId) {
      return res.status(400).json({
        success: false,
        message: 'User ID is required'
      });
    }
    
    const collection = await getMembersCollection();
    const user = await collection.findOne({ user_id: userId });
    
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }
    
    res.status(200).json({
      success: true,
      data: user
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/users
 * Create or update user data
 */
router.post('/', validateUserData, async (req, res, next) => {
  try {
    const { user_id, roles, nickname } = req.body;
    
    const collection = await getMembersCollection();
    
    // Update or insert user data
    const result = await collection.updateOne(
      { user_id },
      { $set: { roles, nickname } },
      { upsert: true }
    );
    
    const isNewUser = result.upsertedCount === 1;
    
    res.status(isNewUser ? 201 : 200).json({
      success: true,
      message: isNewUser ? 'User created' : 'User updated',
      data: { user_id, roles, nickname }
    });
  } catch (error) {
    // Handle duplicate key error
    if (error.code === 11000) {
      return res.status(400).json({
        success: false,
        message: 'Duplicate user ID'
      });
    }
    next(error);
  }
});

/**
 * DELETE /api/users/:id
 * Delete user by ID
 */
router.delete('/:id', async (req, res, next) => {
  try {
    const userId = req.params.id;
    
    // Basic validation
    if (!userId) {
      return res.status(400).json({
        success: false,
        message: 'User ID is required'
      });
    }
    
    const collection = await getMembersCollection();
    const result = await collection.deleteOne({ user_id: userId });
    
    if (result.deletedCount === 0) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }
    
    res.status(200).json({
      success: true,
      message: 'User deleted'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/users
 * Clear all users (Admin only)
 */
router.delete('/', isAdminUser, async (req, res, next) => {
  try {
    const collection = await getMembersCollection();
    const result = await collection.deleteMany({});
    
    res.status(200).json({
      success: true,
      message: 'All users deleted',
      count: result.deletedCount
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;