/**
 * Validate user data for create/update operations
 */
const validateUserData = (req, res, next) => {
    const { user_id, roles } = req.body;
    
    // Check required fields
    if (!user_id) {
      return res.status(400).json({
        success: false,
        message: 'user_id is required'
      });
    }
    
    // Validate user_id format (should be a string with valid characters)
    if (typeof user_id !== 'string' || !/^\d+$/.test(user_id)) {
      return res.status(400).json({
        success: false,
        message: 'user_id must be a valid Discord user ID (string of numbers)'
      });
    }
    
    // Validate roles if provided
    if (roles !== undefined) {
      // Roles should be an array
      if (!Array.isArray(roles)) {
        return res.status(400).json({
          success: false,
          message: 'roles must be an array'
        });
      }
      
      // Validate each role ID
      for (const roleId of roles) {
        if (typeof roleId !== 'string' || !/^\d+$/.test(roleId)) {
          return res.status(400).json({
            success: false,
            message: 'Each role ID must be a valid Discord role ID (string of numbers)'
          });
        }
      }
    }
    
    // All validations passed
    next();
  };
  
  /**
   * Check if user is an admin
   * Currently using the API key approach - all authenticated users
   * can perform admin actions with the full API key
   */
  const isAdminUser = (req, res, next) => {
    // In this implementation, any authenticated user is considered an admin
    // The auth middleware already checked the API key
    // You could implement additional checks here if needed
    
    // For example, you could have a separate ADMIN_API_KEY
    const adminApiKey = process.env.ADMIN_API_KEY;
    
    if (adminApiKey && req.headers['x-api-key'] !== adminApiKey) {
      return res.status(403).json({
        success: false,
        message: 'Admin privileges required'
      });
    }
    
    next();
  };
  
  module.exports = {
    validateUserData,
    isAdminUser
  };