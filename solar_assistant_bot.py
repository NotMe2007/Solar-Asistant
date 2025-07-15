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
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import re

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

try:
    import pytesseract
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    pytesseract = None
    cv2 = None
    np = None
    OCR_AVAILABLE = False

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('solar_assistant_bot.log', encoding='utf-8'),
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
        self.last_system_status = None
        self.last_alert_time = None
        self.status_file = "system_status.json"
        
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
    
    def load_system_status(self):
        """Load the last known system status from file."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    self.last_system_status = status_data.get('status')
                    last_alert_str = status_data.get('last_alert_time')
                    if last_alert_str:
                        self.last_alert_time = datetime.fromisoformat(last_alert_str)
                logger.info(f"Loaded system status: {self.last_system_status}")
        except Exception as e:
            logger.error(f"Error loading system status: {e}")
    
    def save_system_status(self, status: str):
        """Save the current system status to file."""
        try:
            status_data = {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'last_alert_time': self.last_alert_time.isoformat() if self.last_alert_time else None
            }
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            self.last_system_status = status
        except Exception as e:
            logger.error(f"Error saving system status: {e}")
    
    def analyze_dashboard_status(self, screenshot_data):
        """Analyze the dashboard screenshot to detect grid status by looking for the grid indicator."""
        try:
            # Convert screenshot to PIL Image
            image = Image.open(BytesIO(screenshot_data))
            
            # If OCR is available, use it as backup, but focus on visual grid indicator analysis
            if OCR_AVAILABLE and pytesseract and cv2 and np:
                try:
                    # Convert to OpenCV format for better analysis
                    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    
                    # Convert to HSV for better color detection
                    hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
                    
                    # Define color ranges for green checkmark and red X
                    # Green range (for the checkmark)
                    lower_green = np.array([40, 50, 50])
                    upper_green = np.array([80, 255, 255])
                    green_mask = cv2.inRange(hsv, lower_green, upper_green)
                    
                    # Red range (for the X when offline)
                    lower_red1 = np.array([0, 50, 50])
                    upper_red1 = np.array([10, 255, 255])
                    lower_red2 = np.array([170, 50, 50])
                    upper_red2 = np.array([180, 255, 255])
                    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
                    
                    # Count green and red pixels
                    green_pixels = cv2.countNonZero(green_mask)
                    red_pixels = cv2.countNonZero(red_mask)
                    
                    # Look specifically in the grid area (left side of dashboard)
                    height, width = cv_image.shape[:2]
                    grid_area = cv_image[int(height*0.3):int(height*0.7), 0:int(width*0.4)]  # Left side, middle vertical area
                    
                    # Convert grid area to HSV
                    grid_hsv = cv2.cvtColor(grid_area, cv2.COLOR_BGR2HSV)
                    grid_green_mask = cv2.inRange(grid_hsv, lower_green, upper_green)
                    grid_red_mask1 = cv2.inRange(grid_hsv, lower_red1, upper_red1)
                    grid_red_mask2 = cv2.inRange(grid_hsv, lower_red2, upper_red2)
                    grid_red_mask = cv2.bitwise_or(grid_red_mask1, grid_red_mask2)
                    
                    grid_green_pixels = cv2.countNonZero(grid_green_mask)
                    grid_red_pixels = cv2.countNonZero(grid_red_mask)
                    
                    logger.info(f"Grid area analysis - Green pixels: {grid_green_pixels}, Red pixels: {grid_red_pixels}")
                    
                    # Determine status based on color detection in grid area
                    if grid_green_pixels > 50:  # Sufficient green pixels for checkmark
                        return "grid_online"
                    elif grid_red_pixels > 30:  # Red X detected
                        return "grid_offline"
                    else:
                        # Fallback to OCR text analysis
                        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                        text = pytesseract.image_to_string(gray).lower()
                        
                        if any(word in text for word in ['offline', 'disconnected', 'fault', 'error']) and any(word in text for word in ['grid', 'mains', 'utility']):
                            return "grid_offline"
                        else:
                            return "grid_online"
                        
                except Exception as e:
                    logger.warning(f"Advanced visual analysis failed, falling back to simple analysis: {e}")
            
            # Fallback: Simple visual analysis without OpenCV
            logger.info("Using simple visual analysis for grid status detection")
            
            # Convert to RGB for color analysis
            rgb_image = image.convert('RGB')
            width, height = rgb_image.size
            
            # Focus on the left side where the grid indicator should be
            grid_area_pixels = []
            for y in range(int(height * 0.3), int(height * 0.7)):  # Middle vertical area
                for x in range(0, int(width * 0.4)):  # Left side
                    if x < width and y < height:
                        r, g, b = rgb_image.getpixel((x, y))
                        grid_area_pixels.append((r, g, b))
            
            # Count green-ish pixels (for checkmark) and red-ish pixels (for X)
            green_count = 0
            red_count = 0
            
            for r, g, b in grid_area_pixels:
                # Green detection (checkmark)
                if g > r + 20 and g > b + 20 and g > 100:  # More green than red/blue
                    green_count += 1
                # Red detection (X)
                elif r > g + 20 and r > b + 20 and r > 100:  # More red than green/blue
                    red_count += 1
            
            logger.info(f"Simple grid analysis - Green-ish pixels: {green_count}, Red-ish pixels: {red_count}")
            
            # Determine status
            if green_count > 20:  # Found sufficient green pixels for checkmark
                return "grid_online"
            elif red_count > 15:  # Found red pixels for X
                return "grid_offline"
            else:
                # Default to online if we can't detect clearly
                return "grid_online"
                
        except Exception as e:
            logger.error(f"Error analyzing grid status: {e}")
            return "unknown"
    
    def should_send_alert(self, current_status: str) -> bool:
        """Determine if an alert should be sent based on status change and timing."""
        alerts_config = self.config.get('alerts', {})
        
        if not alerts_config.get('enabled', True):
            return False
        
        # Alert on grid status changes
        if current_status == "grid_offline" and self.last_system_status != "grid_offline":
            return True
        
        # Alert on grid recovery
        if current_status == "grid_online" and self.last_system_status == "grid_offline":
            return True
        
        # Check for repeated grid offline alerts (with minimum interval)
        if current_status == "grid_offline" and self.last_alert_time:
            min_interval = alerts_config.get('min_alert_interval_minutes', 30)
            time_since_last_alert = datetime.now() - self.last_alert_time
            if time_since_last_alert.total_seconds() / 60 >= min_interval:
                return True
        
        return False
    
    def send_alert(self, status: str, screenshot_data, filepath):
        """Send an alert webhook for grid status changes."""
        try:
            alerts_config = self.config.get('alerts', {})
            alert_webhook_url = alerts_config.get('webhook_url')
            
            if not alert_webhook_url:
                alert_webhook_url = self.config['webhook']['url']  # Fallback to main webhook
            
            # Prepare custom alert messages
            if status == "grid_offline":
                alert_msg = "<@SeneX> Grid is offline"
                embed_description = "🚨 **GRID OFFLINE ALERT**\n\nThe grid power supply has been detected as offline. The system detected a red X indicator next to the Grid status."
                priority = "HIGH"
                color = 15158332  # Red
            elif status == "grid_online" and self.last_system_status == "grid_offline":
                alert_msg = "<@SeneX> Power is back"
                embed_description = "✅ **POWER RESTORED**\n\nThe grid power supply has been restored. The system detected a green checkmark next to the Grid status."
                priority = "INFO"
                color = 3066993  # Green
            else:
                # Fallback for other status types
                alert_msg = f"<@SeneX> System status update: {status}"
                embed_description = f"ℹ️ System status changed to: {status.replace('_', ' ').title()}"
                priority = "LOW"
                color = 16776960  # Yellow
            
            # For Discord webhooks, send with custom format
            if "discord.com" in alert_webhook_url:
                files = {
                    'file': ('solar_alert.png', BytesIO(screenshot_data), 'image/png')
                }
                
                payload = {
                    'content': alert_msg,
                    'embeds': [{
                        'title': 'Solar Assistant - Grid Status Alert',
                        'description': embed_description,
                        'color': color,
                        'timestamp': datetime.now().isoformat(),
                        'fields': [
                            {'name': 'Grid Status', 'value': status.replace('_', ' ').title(), 'inline': True},
                            {'name': 'Priority', 'value': priority, 'inline': True},
                            {'name': 'Detection Method', 'value': 'Visual Grid Indicator Analysis', 'inline': True},
                            {'name': 'Site', 'value': self.config['solar_assistant']['url'], 'inline': False}
                        ],
                        'image': {'url': 'attachment://solar_alert.png'},
                        'footer': {'text': 'Solar Assistant Bot - Grid Monitor'}
                    }]
                }
                
                response = requests.post(
                    alert_webhook_url,
                    files=files,
                    data={'payload_json': json.dumps(payload)},
                    timeout=30
                )
            else:
                # Generic webhook format
                files = {
                    'file': ('solar_alert.png', BytesIO(screenshot_data), 'image/png')
                }
                
                data = {
                    'alert_type': 'grid_status_change',
                    'status': status,
                    'priority': priority,
                    'message': alert_msg,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Solar Assistant Bot - Grid Monitor',
                    'site': self.config['solar_assistant']['url']
                }
                
                response = requests.post(
                    alert_webhook_url,
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code in [200, 204]:
                logger.info(f"Grid alert sent successfully: {alert_msg}")
                self.last_alert_time = datetime.now()
                return True
            else:
                logger.error(f"Grid alert webhook failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error sending grid alert: {e}")
            return False
    
    def run_capture_cycle(self):
        """Run a complete capture cycle."""
        logger.info("Starting capture cycle")
        
        try:
            # Load last known status before starting
            self.load_system_status()
            
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
            
            # Analyze dashboard status for alerts
            alerts_config = self.config.get('alerts', {})
            if alerts_config.get('enabled', True) and alerts_config.get('check_for_offline', True):
                current_status = self.analyze_dashboard_status(screenshot_data)
                logger.info(f"Current system status: {current_status}")
                
                # Check if we need to send an alert
                if self.should_send_alert(current_status):
                    logger.info("Status change detected - sending alert")
                    alert_success = self.send_alert(current_status, screenshot_data, filepath)
                    if alert_success:
                        self.last_alert_time = datetime.now()
                
                # Save the current status
                self.save_system_status(current_status)
            
            # Send regular webhook
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
