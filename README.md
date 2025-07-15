# Solar-Assistant Bot

An automated webhook system for https://solar-assistant.io/sites that captures dashboard screenshots and sends them via webhooks on a scheduled basis. This bot runs headlessly in the background without requiring the browser to be open on your PC.

## Features

- 🤖 **Automated Screenshots**: Captures full-page screenshots of your Solar Assistant dashboard
- ⏰ **Scheduled Execution**: Runs every hour (configurable) automatically
- 🔐 **Secure Login**: Handles authentication automatically using stored credentials
- 📡 **Webhook Integration**: Sends screenshots via HTTP webhooks to your preferred service
- 🚀 **Headless Operation**: Runs in the background without opening browser windows
- 📝 **Comprehensive Logging**: Detailed logs for monitoring and troubleshooting
- 🖼️ **Local Backup**: Saves screenshots locally with timestamps

## Quick Start

### Windows Users (Easiest)
1. Double-click `setup.bat` to automatically install and configure everything
2. Follow the prompts to enter your credentials and webhook URL
3. Double-click `run_bot.bat` to start the bot

### Manual Setup

#### Prerequisites
- Python 3.7+
- Google Chrome browser
- ChromeDriver (automatically detected or install separately)

#### Installation

1. **Clone or download this repository**
   ```powershell
   git clone <repository-url>
   cd Solar-Asistant
   ```

2. **Install Python dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Install ChromeDriver**
   - **Option 1**: Download from [ChromeDriver Downloads](https://chromedriver.chromium.org/) and add to PATH
   - **Option 2**: Install via Chocolatey: `choco install chromedriver`
   - **Option 3**: Use webdriver-manager: `pip install webdriver-manager`

4. **Configure the bot**
   ```powershell
   python setup.py
   ```
   Or manually edit `config.json` with your credentials

## Configuration

Edit `config.json` to customize the bot behavior:

```json
{
  "solar_assistant": {
    "url": "https://the-incredibles.za.solar-assistant.io/",
    "username": "your_username_here",
    "password": "your_password_here"
  },
  "webhook": {
    "url": "https://your-webhook-url-here.com/webhook",
    "method": "POST",
    "headers": {
      "Content-Type": "multipart/form-data"
    }
  },
  "schedule": {
    "interval_hours": 1,
    "enabled": true
  },
  "screenshot": {
    "wait_time_seconds": 10,
    "full_page": true,
    "quality": 90
  }
}
```

### Configuration Options

| Section | Setting | Description | Default |
|---------|---------|-------------|---------|
| `solar_assistant` | `url` | Your Solar Assistant dashboard URL | - |
| `solar_assistant` | `username` | Your login username/email | - |
| `solar_assistant` | `password` | Your login password | - |
| `webhook` | `url` | Webhook endpoint to send screenshots | - |
| `webhook` | `method` | HTTP method for webhook | `POST` |
| `schedule` | `interval_hours` | Hours between captures | `1` |
| `schedule` | `enabled` | Enable/disable scheduling | `true` |
| `screenshot` | `wait_time_seconds` | Wait time for page load | `10` |
| `screenshot` | `full_page` | Capture full page vs viewport | `true` |
| `screenshot` | `quality` | Image quality (1-100) | `90` |

## Usage

### Running the Bot

**Scheduled Mode (Continuous)**:
```powershell
python solar_assistant_bot.py
```

**Test Mode (Single Capture)**:
```powershell
python solar_assistant_bot.py --test
```

**Windows Batch Files**:
- `run_bot.bat` - Start the bot in scheduled mode
- `setup.bat` - Run the setup wizard

### Webhook Format

The bot sends screenshots as multipart/form-data with the following fields:
- `file`: The screenshot image (PNG format)
- `timestamp`: ISO format timestamp
- `source`: "Solar Assistant Bot"
- `site`: The Solar Assistant URL

### Logs

The bot creates detailed logs in `solar_assistant_bot.log` including:
- Login attempts and results
- Screenshot capture status
- Webhook delivery status
- Error messages and debugging info

### Screenshots

Local screenshots are saved to the `screenshots/` directory with timestamp filenames:
```
screenshots/
├── solar_dashboard_20250715_140000.png
├── solar_dashboard_20250715_150000.png
└── ...
```

## Troubleshooting

### Common Issues

**ChromeDriver not found**:
- Ensure ChromeDriver is installed and in your PATH
- Or use the webdriver-manager package: `pip install webdriver-manager`

**Login failing**:
- Verify credentials in `config.json`
- Check if Solar Assistant site structure has changed
- Review logs for specific error messages

**Webhook not sending**:
- Verify webhook URL is correct and accessible
- Check webhook service logs for errors
- Test webhook endpoint manually

**Screenshots empty or incorrect**:
- Increase `wait_time_seconds` in config
- Check if login is successful
- Verify Solar Assistant dashboard loads correctly

### Getting Help

1. Check the log file `solar_assistant_bot.log` for detailed error messages
2. Run in test mode to debug issues: `python solar_assistant_bot.py --test`
3. Verify configuration with `python setup.py`

## Security Notes

- Store credentials securely and don't commit `config.json` to version control
- Use environment variables for sensitive data in production
- Consider using webhook authentication/tokens
- Regularly rotate passwords

## Requirements

- Python 3.7+
- selenium==4.21.0
- requests==2.31.0
- Pillow==10.3.0
- schedule==1.2.0
- python-dotenv==1.0.1
- Google Chrome browser
- ChromeDriver

## License

This project is provided as-is for personal use with Solar Assistant dashboards.
