#!/usr/bin/env python3
"""
Solar Assistant Webhook Bot
Automatically captures screenshots of Solar Assistant dashboard and sends them via webhook.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import requests
import schedule
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('solar_assistant_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SolarAssistantBot:
    def __init__(self, config_path="config.json"):
        """Initialize the bot with configuration."""
        self.config_path = config_path
        self.config = self.load_config()
        self.driver: Optional[webdriver.Chrome] = None
        
    def load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info("Configuration loaded successfully")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file {self.config_path}")
            raise
    
    def setup_driver(self):
        """Setup Chrome driver with headless options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Optional: disable images for faster loading
            
            # Try to use Chrome driver
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver initialized successfully")
            
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            logger.info("Please make sure ChromeDriver is installed and in PATH")
            raise
    
    def login_to_solar_assistant(self):
        """Login to Solar Assistant dashboard."""
        if self.driver is None:
            logger.error("Driver not initialized")
            return False
            
        try:
            url = self.config['solar_assistant']['url']
            username = self.config['solar_assistant']['username']
            password = self.config['solar_assistant']['password']
            
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 30)  # Increased timeout
            
            # Try to find login form elements with Solar Assistant specific selectors
            try:
                # First, let's check if we're already logged in
                current_url = self.driver.current_url.lower()
                if "sign_in" not in current_url and "login" not in current_url:
                    logger.info("Already appears to be logged in or on dashboard")
                    return True
                
                # Wait for page to fully load
                time.sleep(3)
                
                # Solar Assistant specific selectors
                try:
                    # Look for the specific email field used by Solar Assistant
                    username_field = wait.until(
                        EC.presence_of_element_located((By.NAME, "user[email]"))
                    )
                    logger.info("Found email field")
                except TimeoutException:
                    try:
                        username_field = wait.until(
                            EC.presence_of_element_located((By.ID, "user_email"))
                        )
                        logger.info("Found email field by ID")
                    except TimeoutException:
                        logger.error("Could not find email input field")
                        self.driver.save_screenshot("debug_login_page.png")
                        logger.info("Saved debug screenshot as debug_login_page.png")
                        return False
                
                # Look for the specific password field used by Solar Assistant
                try:
                    password_field = self.driver.find_element(By.NAME, "user[password]")
                    logger.info("Found password field")
                except:
                    try:
                        password_field = self.driver.find_element(By.ID, "user_password")
                        logger.info("Found password field by ID")
                    except:
                        logger.error("Could not find password input field")
                        self.driver.save_screenshot("debug_login_page.png")
                        logger.info("Saved debug screenshot as debug_login_page.png")
                        return False
                
                # Clear and enter credentials
                logger.info("Entering credentials...")
                username_field.clear()
                username_field.send_keys(username)
                
                password_field.clear()
                password_field.send_keys(password)
                
                # Find and click the Solar Assistant submit button
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    logger.info("Found submit button")
                    login_button.click()
                    logger.info("Clicked submit button")
                except:
                    try:
                        # Alternative: submit the form directly
                        password_field.submit()
                        logger.info("Submitted form directly")
                    except:
                        logger.error("Could not submit login form")
                        return False
                
                # Wait for redirect or dashboard to load
                logger.info("Waiting for login to complete...")
                time.sleep(8)
                
                # Check if login was successful - Solar Assistant redirects to the user's specific dashboard
                current_url = self.driver.current_url.lower()
                if "sign_in" not in current_url and "login" not in current_url:
                    # Should be redirected to something like https://the-incredibles.za.solar-assistant.io/
                    logger.info(f"Login successful - redirected to: {self.driver.current_url}")
                    return True
                else:
                    logger.error("Login failed - still on login page")
                    # Save debug screenshot
                    self.driver.save_screenshot("debug_login_failed.png")
                    logger.info("Saved debug screenshot as debug_login_failed.png")
                    return False
                    
            except TimeoutException:
                logger.warning("Could not find login form - checking if already logged in")
                # Maybe already logged in or different page structure
                return True
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def capture_screenshot(self):
        """Capture screenshot of the dashboard."""
        if self.driver is None:
            logger.error("Driver not initialized")
            return None, None
            
        try:
            # Wait for dashboard to fully load
            wait_time = self.config['screenshot']['wait_time_seconds']
            logger.info(f"Waiting {wait_time} seconds for dashboard to load")
            time.sleep(wait_time)
            
            # Take screenshot
            if self.config['screenshot']['full_page']:
                # Get full page screenshot
                screenshot = self.driver.get_screenshot_as_png()
            else:
                # Get viewport screenshot
                screenshot = self.driver.get_screenshot_as_png()
            
            # Process image if needed
            image = Image.open(BytesIO(screenshot))
            
            # Save locally with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"solar_dashboard_{timestamp}.png"
            
            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)
            filepath = os.path.join("screenshots", filename)
            
            image.save(filepath, "PNG", quality=self.config['screenshot']['quality'])
            logger.info(f"Screenshot saved: {filepath}")
            
            return screenshot, filepath
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None, None
    
    def send_webhook(self, screenshot_data, filepath):
        """Send screenshot via webhook."""
        try:
            webhook_config = self.config['webhook']
            webhook_url = webhook_config['url']
            
            if not webhook_url or webhook_url == "https://your-webhook-url-here.com/webhook":
                logger.warning("Webhook URL not configured - skipping webhook send")
                return False
            
            # Prepare the file for upload
            files = {
                'file': ('solar_dashboard.png', BytesIO(screenshot_data), 'image/png')
            }
            
            # Prepare additional data
            data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'Solar Assistant Bot',
                'site': self.config['solar_assistant']['url']
            }
            
            # Send POST request
            response = requests.post(
                webhook_url,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Webhook sent successfully")
                return True
            else:
                logger.error(f"Webhook failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error sending webhook: {e}")
            return False
    
    def run_capture_cycle(self):
        """Run a complete capture cycle."""
        logger.info("Starting capture cycle")
        
        try:
            # Setup driver
            self.setup_driver()
            
            # Login
            if not self.login_to_solar_assistant():
                logger.error("Login failed - aborting capture cycle")
                return False
            
            # Capture screenshot
            screenshot_data, filepath = self.capture_screenshot()
            
            if screenshot_data is None:
                logger.error("Screenshot capture failed - aborting cycle")
                return False
            
            # Send webhook
            webhook_success = self.send_webhook(screenshot_data, filepath)
            
            logger.info(f"Capture cycle completed - Webhook: {'Success' if webhook_success else 'Failed'}")
            return True
            
        except Exception as e:
            logger.error(f"Error in capture cycle: {e}")
            return False
            
        finally:
            # Clean up driver
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def start_scheduler(self):
        """Start the scheduled execution."""
        if not self.config['schedule']['enabled']:
            logger.info("Scheduler is disabled in configuration")
            return
        
        interval_hours = self.config['schedule']['interval_hours']
        logger.info(f"Starting scheduler - will run every {interval_hours} hour(s)")
        
        # Schedule the job
        schedule.every(interval_hours).hours.do(self.run_capture_cycle)
        
        # Run immediately on start
        logger.info("Running initial capture cycle")
        self.run_capture_cycle()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point."""
    logger.info("Solar Assistant Bot starting")
    
    try:
        bot = SolarAssistantBot()
        
        # Check if running in test mode
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            logger.info("Running in test mode - single capture")
            bot.run_capture_cycle()
        else:
            logger.info("Starting scheduled mode")
            bot.start_scheduler()
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
