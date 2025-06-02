import os
import logging
from flask import Flask, jsonify, request, render_template
from scraper import RobloxScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize scraper
scraper = RobloxScraper()

@app.route('/')
def index():
    """Render the API documentation page"""
    return render_template('index.html')

@app.route('/api/followers/<int:user_id>')
def get_followers(user_id):
    """
    Get follower count for a Roblox user
    
    Args:
        user_id (int): Roblox user ID
        
    Returns:
        JSON response with follower count or error
    """
    logger.info(f"Received request for user ID: {user_id}")
    
    try:
        # Validate user ID
        if user_id <= 0:
            logger.warning(f"Invalid user ID: {user_id}")
            return jsonify({
                'error': 'Invalid user ID',
                'message': 'User ID must be a positive integer'
            }), 400
        
        # Get follower count
        result = scraper.get_user_followers(user_id)
        
        if result['success']:
            logger.info(f"Successfully scraped followers for user {user_id}: {result['followers']}")
            return jsonify({
                'user_id': user_id,
                'followers': result['followers'],
                'username': result.get('username', 'Unknown'),
                'timestamp': result.get('timestamp')
            })
        else:
            logger.error(f"Failed to scrape user {user_id}: {result['error']}")
            return jsonify({
                'error': result['error'],
                'user_id': user_id
            }), 404
            
    except ValueError as e:
        logger.error(f"ValueError for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Invalid user ID format',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing your request'
        }), 500

@app.route('/api/followers')
def get_followers_query():
    """
    Get follower count for a Roblox user using query parameter
    
    Query Parameters:
        user_id (int): Roblox user ID
        
    Returns:
        JSON response with follower count or error
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'error': 'Missing user_id parameter',
            'message': 'Please provide a user_id query parameter'
        }), 400
    
    try:
        user_id = int(user_id)
        return get_followers(user_id)
    except ValueError:
        return jsonify({
            'error': 'Invalid user_id format',
            'message': 'user_id must be a valid integer'
        }), 400

@app.route('/api/cache/clear')
def clear_cache():
    """Clear the scraper cache"""
    try:
        scraper.clear_cache()
        logger.info("Cache cleared successfully")
        return jsonify({
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({
            'error': 'Failed to clear cache',
            'message': str(e)
        }), 500

@app.route('/api/cache/stats')
def cache_stats():
    """Get cache statistics"""
    try:
        stats = scraper.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return jsonify({
            'error': 'Failed to get cache stats',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
