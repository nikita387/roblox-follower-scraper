import requests
import re
import time
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RobloxScraper:
    def __init__(self):
        """
        Initialize the Roblox scraper
        """
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.base_url = "https://www.roblox.com/users/{}/profile"
        

    
    def get_user_followers(self, user_id: int) -> Dict[str, Any]:
        """
        Get follower count for a Roblox user
        
        Args:
            user_id: Roblox user ID
            
        Returns:
            Dictionary with success status, follower count, and other data
        """
        try:
            # Get user info from Roblox API (no caching)
            username = self._get_username_from_api(user_id)
            followers = self._get_followers_from_api(user_id)
            
            if username and followers is not None:
                result = {
                    'success': True,
                    'user_id': user_id,
                    'username': username,
                    'followers': followers,
                    'timestamp': datetime.now().isoformat()
                }
                return result
            
            # Fallback to web scraping if API fails
            return self._scrape_user_profile(user_id)
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while getting user {user_id}")
            return {
                'success': False,
                'error': 'Request timeout - Roblox servers may be slow',
                'user_id': user_id
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while getting user {user_id}")
            return {
                'success': False,
                'error': 'Unable to connect to Roblox servers',
                'user_id': user_id
            }
        except Exception as e:
            logger.error(f"Unexpected error while getting user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
                'user_id': user_id
            }
    
    def _get_username_from_api(self, user_id: int) -> Optional[str]:
        """Get username using Roblox API"""
        try:
            url = f"https://users.roblox.com/v1/users/{user_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('name', data.get('displayName'))
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"API returned status {response.status_code} for user {user_id}")
                return None
        except Exception as e:
            logger.warning(f"Failed to get username from API for user {user_id}: {str(e)}")
            return None
    
    def _get_followers_from_api(self, user_id: int) -> Optional[int]:
        """Get follower count using Roblox API"""
        try:
            # Try the friends API first
            url = f"https://friends.roblox.com/v1/users/{user_id}/followers/count"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('count', 0)
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:
                # Rate limited - wait a bit and try once more
                logger.info(f"Rate limited for user {user_id}, waiting 2 seconds...")
                time.sleep(2)
                
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('count', 0)
                else:
                    logger.warning(f"Still rate limited after retry for user {user_id}")
                    return None
            else:
                logger.warning(f"Followers API returned status {response.status_code} for user {user_id}")
                return None
        except Exception as e:
            logger.warning(f"Failed to get followers from API for user {user_id}: {str(e)}")
            return None
    
    def _scrape_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Fallback method to scrape user profile from web page"""
        try:
            # Construct profile URL
            url = self.base_url.format(user_id)
            logger.debug(f"Scraping URL: {url}")
            
            # Make request with timeout
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if user exists by looking for error indicators
            if "User not found" in response.text or response.status_code == 404:
                return {
                    'success': False,
                    'error': 'User not found',
                    'user_id': user_id
                }
            
            # Extract username
            username = self._extract_username(soup)
            
            # Extract follower count
            followers = self._extract_followers(soup)
            
            if followers is None:
                return {
                    'success': False,
                    'error': 'Could not extract follower count from profile page',
                    'user_id': user_id,
                    'username': username
                }
            
            result = {
                'success': True,
                'user_id': user_id,
                'username': username,
                'followers': followers,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while scraping user {user_id}")
            return {
                'success': False,
                'error': 'Request timeout - Roblox servers may be slow',
                'user_id': user_id
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while scraping user {user_id}")
            return {
                'success': False,
                'error': 'Unable to connect to Roblox servers',
                'user_id': user_id
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    'success': False,
                    'error': 'User not found',
                    'user_id': user_id
                }
            logger.error(f"HTTP error {e.response.status_code} while scraping user {user_id}")
            return {
                'success': False,
                'error': f'HTTP error: {e.response.status_code}',
                'user_id': user_id
            }
        except Exception as e:
            logger.error(f"Unexpected error while scraping user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred during scraping',
                'user_id': user_id
            }
    
    def _extract_username(self, soup: BeautifulSoup) -> str:
        """Extract username from profile page"""
        try:
            # Strategy 1: Extract from page title
            title = soup.find('title')
            if title:
                title_text = title.get_text().strip()
                # Title format is usually "Username - Roblox"
                if ' - Roblox' in title_text:
                    username = title_text.replace(' - Roblox', '').strip()
                    if username and len(username) < 50:
                        return username
            
            # Strategy 2: Extract from meta description
            try:
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    content = meta_desc.get('content', '')
                    if content and ' is one of the millions' in str(content):
                        username = str(content).split(' is one of the millions')[0].strip()
                        if username and len(username) < 50:
                            return username
            except:
                pass
            
            # Strategy 3: Extract from Open Graph title
            try:
                og_title = soup.find('meta', {'property': 'og:title'})
                if og_title:
                    content = og_title.get('content', '')
                    if content and "'s Profile" in str(content):
                        username = str(content).replace("'s Profile", '').strip()
                        if username and len(username) < 50:
                            return username
            except:
                pass
            
            # Strategy 4: Try common selectors for username
            selectors = [
                'h1[data-testid="profile-display-name"]',
                '.profile-display-name',
                '.profile-name h1',
                'h1.profile-name',
                '.header-title h1',
                '.profile-header h1',
                '.profile-card h1'
            ]
            
            for selector in selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        username = element.get_text().strip()
                        if username and len(username) < 50:
                            return username
                except:
                    continue
            
            # Strategy 5: Look for any h1 that might contain the username
            try:
                h1_elements = soup.find_all('h1')
                for h1 in h1_elements:
                    text = h1.get_text().strip()
                    if text and len(text) < 50 and not any(word in text.lower() for word in ['roblox', 'profile', 'error', 'not found']):
                        return text
            except:
                pass
                    
            return "Unknown"
        except Exception as e:
            logger.warning(f"Could not extract username: {str(e)}")
            return "Unknown"
    
    def _extract_followers(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract follower count from profile page"""
        try:
            # Strategy 1: Look in script tags for JSON data with follower information
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_content = None
                if hasattr(script, 'string') and script.string:
                    script_content = script.string
                elif script.get_text():
                    script_content = script.get_text()
                
                if script_content:
                    # Look for follower data in JavaScript variables or JSON
                    follower_patterns = [
                        r'"[Ff]ollowersCount":\s*(\d+)',
                        r'"[Ff]ollowers":\s*(\d+)',
                        r'"[Ff]ollowerCount":\s*(\d+)',
                        r'followersCount["\']:\s*(\d+)',
                        r'followers["\']:\s*(\d+)',
                        r'FollowersCount["\']:\s*(\d+)',
                    ]
                    
                    for pattern in follower_patterns:
                        matches = re.findall(pattern, script_content)
                        if matches:
                            return int(matches[0])
            
            # Strategy 2: Look for specific data attributes or classes in newer Roblox layout
            follower_selectors = [
                '[data-testid="followers-count"]',
                '[data-testid="follower-count"]',
                '.followers-count',
                '.follower-count',
                '.profile-stats-followers',
                '.followers .stat-value',
                '.stat-followers .stat-value',
                '.profile-stat-followers',
                '[class*="follower"] .text-label',
                '[class*="follower"] .font-header-2'
            ]
            
            for selector in follower_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and re.search(r'\d', text):
                        follower_count = self._parse_number(text)
                        if follower_count >= 0:
                            return follower_count
            
            # Strategy 3: Look for text patterns that indicate followers
            page_text = soup.get_text()
            text_patterns = [
                r'(\d+(?:,\d+)*)\s*[Ff]ollowers?',
                r'[Ff]ollowers?:\s*(\d+(?:,\d+)*)',
                r'(\d+(?:,\d+)*)\s*people\s+follow',
                r'(\d+(?:,\d+)*)\s*[Ff]ollowing\s+you',
                r'(\d+(?:\.\d*)?[KkMmBb]?)\s*[Ff]ollowers?'
            ]
            
            for pattern in text_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    for match in matches:
                        follower_count = self._parse_number(match)
                        if follower_count >= 0:
                            return follower_count
            
            # Strategy 4: Look for numbers near follower-related text
            follower_context_patterns = [
                r'(?i:followers?|following)[^\d]*(\d+(?:,\d+)*|\d+(?:\.\d+)?[kmb]?)',
                r'(\d+(?:,\d+)*|\d+(?:\.\d+)?[kmb]?)[^\d]*(?i:followers?|following)'
            ]
            
            for pattern in follower_context_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    for match in matches:
                        follower_count = self._parse_number(match)
                        if follower_count >= 0:
                            return follower_count
            
            # Strategy 5: Last resort - look for reasonable numbers that might be follower counts
            # Only use this if we found very specific indicators
            if 'profile' in page_text.lower() and 'roblox' in page_text.lower():
                number_patterns = [
                    r'\b(\d{1,3}(?:,\d{3})+)\b',  # Numbers with commas (like 1,234)
                    r'\b(\d+(?:\.\d+)?[KkMmBb])\b'  # Numbers with K/M/B suffix
                ]
                
                potential_followers = []
                for pattern in number_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        count = self._parse_number(match)
                        if 0 <= count <= 100000000:  # Reasonable range for followers
                            potential_followers.append(count)
                
                if potential_followers:
                    logger.warning(f"Using heuristic follower count detection")
                    # Return the most reasonable number (prefer larger numbers that are more likely to be follower counts)
                    potential_followers.sort(reverse=True)
                    return potential_followers[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting followers: {str(e)}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """Parse a number string that might contain commas"""
        try:
            # Remove commas and other non-digit characters except for k, m, b suffixes
            text = text.strip().lower()
            
            # Handle k, m, b suffixes
            multiplier = 1
            if text.endswith('k'):
                multiplier = 1000
                text = text[:-1]
            elif text.endswith('m'):
                multiplier = 1000000
                text = text[:-1]
            elif text.endswith('b'):
                multiplier = 1000000000
                text = text[:-1]
            
            # Remove commas and convert to int
            number_str = re.sub(r'[^\d.]', '', text)
            if '.' in number_str:
                return int(float(number_str) * multiplier)
            else:
                return int(number_str) * multiplier
        except (ValueError, AttributeError):
            return 0
    
    def clear_cache(self) -> None:
        """Cache system has been removed for real-time data"""
        logger.info("Cache system removed - all requests now fetch real-time data")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'message': 'Cache system has been removed for real-time follower tracking',
            'total_entries': 0,
            'valid_entries': 0,
            'expired_entries': 0,
            'cache_enabled': False
        }
