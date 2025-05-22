require('dotenv').config();

/**
 * API Authentication Middleware
 * Validates API key or JWT token for protected routes
 */
const authMiddleware = (req, res, next) => {
  // Skip authentication for health check route
  if (req.path === '/health') {
    return next();
  }
  
  // Get API key from environment
  const validApiKey = process.env.API_KEY;
  
  // If no API key is configured, warn but allow access in development
  if (!validApiKey) {
    if (process.env.NODE_ENV === 'production') {
      console.error('ERROR: No API_KEY set in production mode');
      return res.status(500).json({
        success: false,
        message: 'Server configuration error'
      });
    } else {
      console.warn('WARNING: No API_KEY set, authentication disabled');
      return next();
    }
  }
  
  // Check for API key in headers
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({
      success: false,
      message: 'API key is missing'
    });
  }
  
  // Validate API key
  if (apiKey !== validApiKey) {
    return res.status(403).json({
      success: false,
      message: 'Invalid API key'
    });
  }
  
  // API key is valid, proceed
  next();
};

module.exports = authMiddleware;