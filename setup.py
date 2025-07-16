#!/usr/bin/env python3
"""
Setup script for Solar Assistant Bot
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def install_requirements():
    """Install required Python packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False


def check_chromedriver():
    """Check if ChromeDriver is available."""
    print("Checking ChromeDriver availability...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        print("✓ ChromeDriver is available")
        return True
    except Exception as e:
        print(f"✗ ChromeDriver not available: {e}")
        print("\nTo install ChromeDriver:")
        print("1. Download from: https://chromedriver.chromium.org/")
        print("2. Or install via: pip install webdriver-manager")
        print("3. Or on Windows with Chocolatey: choco install chromedriver")
        return False


def setup_config():
    """Help user setup configuration."""
    config_file = "config.json"
    
    if os.path.exists(config_file):
        print(f"✓ Configuration file {config_file} already exists")
        
        # Ask if user wants to update it
        update = input("Do you want to update the configuration? (y/n): ").lower().strip()
        if update != 'y':
            return True
    
    print("\nSetting up configuration...")
    print("Please provide the following information:")
    
    # Get user inputs
    solar_url = input("Solar Assistant URL [https://solar-assistant.io/]: ").strip()
    if not solar_url:
        solar_url = "https://solar-assistant.io/"
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    webhook_url = input("Webhook URL (optional, leave empty to skip): ").strip()
    if not webhook_url:
        webhook_url = "https://your-webhook-url-here.com/webhook"
    
    interval = input("Capture interval in hours [1]: ").strip()
    if not interval:
        interval = 1
    else:
        try:
            interval = int(interval)
        except ValueError:
            interval = 1
    
    # Create configuration
    config = {
        "solar_assistant": {
            "url": solar_url,
            "username": username,
            "password": password
        },
        "webhook": {
            "url": webhook_url,
            "method": "POST",
            "headers": {
                "Content-Type": "multipart/form-data"
            }
        },
        "schedule": {
            "interval_hours": interval,
            "enabled": True
        },
        "screenshot": {
            "wait_time_seconds": 10,
            "full_page": True,
            "quality": 90
        }
    }
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Configuration saved to {config_file}")
        return True
    except Exception as e:
        print(f"✗ Failed to save configuration: {e}")
        return False


def main():
    """Main setup function."""
    print("Solar Assistant Bot Setup")
    print("=" * 25)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    print()
    
    # Check ChromeDriver
    if not check_chromedriver():
        success = False
    
    print()
    
    # Setup configuration
    if not setup_config():
        success = False
    
    print()
    
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review and update config.json if needed")
        print("2. Run the bot in test mode: python solar_assistant_bot.py --test")
        print("3. Run the bot normally: python solar_assistant_bot.py")
    else:
        print("✗ Setup completed with errors. Please address the issues above.")
    
    return success


if __name__ == "__main__":
    main()
