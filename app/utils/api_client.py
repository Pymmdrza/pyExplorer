import requests
import logging
from typing import Optional, Dict, Any
from app.config.config_manager import config

def make_request(url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Make API request with fallback support"""
    for attempt in range(max_retries):
        try:
            logging.info(f"Making API request to: {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=10)  # Add timeout

            if response.status_code == 200:
                logging.info("API request successful")
                return response.json()
            elif response.status_code == 503:  # Service unavailable
                logging.warning(f"Service unavailable (503) on attempt {attempt + 1}")
            else:
                logging.error(f"API request failed with status code: {response.status_code}")
                logging.error(f"Response content: {response.text[:200]}...")  # Log first 200 chars
                break  # Don't retry on non-503 errors

        except requests.exceptions.Timeout:
            logging.error("API request timed out")
        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {str(e)}")
        except ValueError as e:  # JSON decode error
            logging.error(f"Error parsing API response: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error during API request: {str(e)}")

        # Try next node
        if config.fallback_to_next_node():
            logging.info("Switching to fallback node")
            continue
        else:
            logging.error("No more fallback nodes available")
            break

    return None