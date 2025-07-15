#!/usr/bin/env python3
"""
Debug script for Solar Assistant login
This script will help identify the correct selectors for the login form.
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def debug_login_page():
    """Debug the login page to find correct selectors."""
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Please run setup.py first to create config.json")
        return
    
    # Setup Chrome with visible window for debugging
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    # Remove headless for debugging
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = config['solar_assistant']['url']
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Save initial page screenshot
        driver.save_screenshot("debug_page_initial.png")
        print("Saved initial page screenshot")
        
        # Try to find all input elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(inputs)} input elements:")
        
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type") or "text"
            input_name = inp.get_attribute("name") or ""
            input_id = inp.get_attribute("id") or ""
            input_class = inp.get_attribute("class") or ""
            input_placeholder = inp.get_attribute("placeholder") or ""
            
            print(f"  {i+1}. Type: {input_type}, Name: {input_name}, ID: {input_id}")
            print(f"      Class: {input_class}")
            print(f"      Placeholder: {input_placeholder}")
            print()
        
        # Try to find all button elements
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {buttons.__len__()} button elements:")
        
        for i, btn in enumerate(buttons):
            button_type = btn.get_attribute("type") or ""
            button_text = btn.text or ""
            button_class = btn.get_attribute("class") or ""
            
            print(f"  {i+1}. Type: {button_type}, Text: '{button_text}', Class: {button_class}")
        
        # Look for forms
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"\nFound {len(forms)} form elements:")
        
        for i, form in enumerate(forms):
            form_action = form.get_attribute("action") or ""
            form_method = form.get_attribute("method") or ""
            form_class = form.get_attribute("class") or ""
            
            print(f"  {i+1}. Action: {form_action}, Method: {form_method}, Class: {form_class}")
        
        # Get page source for manual inspection
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\nSaved page source to debug_page_source.html")
        
        print("\nPlease check the generated files:")
        print("- debug_page_initial.png (screenshot)")
        print("- debug_page_source.html (page source)")
        print("\nUse this information to update the login selectors in the main script.")
        
        # Keep browser open for manual inspection
        input("\nPress Enter to close the browser...")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    debug_login_page()
