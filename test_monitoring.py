#!/usr/bin/env python3
"""
Simple status monitoring script for Solar Assistant
This version uses basic image analysis instead of OCR for broader compatibility.
"""

import json
import os
from datetime import datetime
from PIL import Image, ImageStat
import requests
from io import BytesIO


def analyze_screenshot_simple(screenshot_path):
    """
    Simple image analysis to detect potential issues.
    This looks for visual indicators rather than text.
    """
    try:
        image = Image.open(screenshot_path)
        
        # Convert to grayscale for analysis
        gray_image = image.convert('L')
        
        # Calculate image statistics
        stat = ImageStat.Stat(gray_image)
        
        # Basic analysis - very dark images might indicate offline status
        mean_brightness = stat.mean[0]
        
        # Save some metadata for debugging
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'mean_brightness': mean_brightness,
            'image_size': image.size,
            'status': 'unknown'
        }
        
        # Very simple heuristic - if image is very dark, might be offline
        if mean_brightness < 50:  # Very dark
            analysis_result['status'] = 'possibly_offline'
            analysis_result['reason'] = 'Very dark image detected'
        elif mean_brightness > 200:  # Very bright/white
            analysis_result['status'] = 'possibly_error'
            analysis_result['reason'] = 'Very bright/white image detected'
        else:
            analysis_result['status'] = 'normal'
            analysis_result['reason'] = 'Normal brightness levels'
        
        print(f"Image Analysis Results:")
        print(f"  Brightness: {mean_brightness:.1f}")
        print(f"  Status: {analysis_result['status']}")
        print(f"  Reason: {analysis_result['reason']}")
        
        return analysis_result
        
    except Exception as e:
        print(f"Error analyzing screenshot: {e}")
        return None


def send_test_alert(webhook_url, message, image_path):
    """Send a test alert to Discord webhook."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        files = {
            'file': ('solar_test.png', image_data, 'image/png')
        }
        
        payload = {
            'content': message,
            'embeds': [{
                'title': 'Solar Assistant Status Test',
                'description': message,
                'color': 15158332,  # Red color
                'timestamp': datetime.now().isoformat(),
                'image': {'url': 'attachment://solar_test.png'}
            }]
        }
        
        response = requests.post(
            webhook_url,
            files=files,
            data={'payload_json': json.dumps(payload)},
            timeout=30
        )
        
        if response.status_code in [200, 204]:
            print("✅ Test alert sent successfully!")
            return True
        else:
            print(f"❌ Alert failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test alert: {e}")
        return False


def main():
    """Test the monitoring functionality."""
    print("Solar Assistant Status Monitor Test")
    print("=" * 40)
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please run setup.py first.")
        return
    
    # Check for recent screenshots
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        print("❌ No screenshots directory found. Run the bot first to capture screenshots.")
        return
    
    # Find the most recent screenshot
    screenshot_files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
    if not screenshot_files:
        print("❌ No screenshot files found. Run the bot first to capture screenshots.")
        return
    
    latest_screenshot = max(screenshot_files, key=lambda x: os.path.getctime(os.path.join(screenshots_dir, x)))
    screenshot_path = os.path.join(screenshots_dir, latest_screenshot)
    
    print(f"📸 Analyzing latest screenshot: {latest_screenshot}")
    
    # Analyze the screenshot
    analysis = analyze_screenshot_simple(screenshot_path)
    
    if analysis:
        # Test alert if configured
        alerts_config = config.get('alerts', {})
        if alerts_config.get('enabled', False):
            webhook_url = alerts_config.get('webhook_url') or config.get('webhook', {}).get('url')
            
            if webhook_url and "discord.com" in webhook_url:
                print(f"\n🧪 Testing alert webhook...")
                test_message = f"🧪 **Status Monitor Test**\n\nAnalyzed: {latest_screenshot}\nStatus: {analysis['status']}\nBrightness: {analysis['mean_brightness']:.1f}\nReason: {analysis['reason']}"
                send_test_alert(webhook_url, test_message, screenshot_path)
            else:
                print("⚠️ No Discord webhook configured for alerts")
        else:
            print("⚠️ Alerts are disabled in config")
    
    print("\n💡 Tips:")
    print("- Enable OCR libraries (pytesseract, opencv-python) for better status detection")
    print("- The bot will automatically monitor for grid offline status")
    print("- Check config.json alerts section for configuration options")


if __name__ == "__main__":
    main()
