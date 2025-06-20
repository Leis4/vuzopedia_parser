import pickle
import os
import logging

logger = logging.getLogger(__name__)

def save_cookies(driver, path):
    try:
        cookies = driver.get_cookies()
        with open(path, "wb") as f:
            pickle.dump(cookies, f)
        logger.info(f"Cookies saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")

def load_cookies(driver, path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"No cookies file at {path}")
    try:
        with open(path, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Failed to add cookie {cookie}: {e}")
        logger.info(f"Loaded cookies from {path}")
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        raise
