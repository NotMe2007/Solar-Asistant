"""
Tests for Solar Assistant Bot
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestConfigLoading:
    """Tests for configuration loading functionality."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        config_data = {
            "solar_assistant": {
                "url": "https://example.com",
                "username": "test_user",
                "password": "test_pass"
            },
            "webhook": {
                "url": "https://webhook.example.com",
                "method": "POST",
                "headers": {"Content-Type": "multipart/form-data"}
            },
            "alerts": {
                "enabled": True,
                "webhook_url": "https://alerts.example.com",
                "check_for_offline": True,
                "min_alert_interval_minutes": 30
            },
            "schedule": {
                "interval_hours": 1,
                "enabled": True
            },
            "screenshot": {
                "wait_time_seconds": 10,
                "full_page": True,
                "quality": 90
            }
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Import after creating config to avoid issues
        from solar_assistant_bot import SolarAssistantBot
        
        bot = SolarAssistantBot(config_path=str(config_path))
        
        assert bot.config['solar_assistant']['url'] == "https://example.com"
        assert bot.config['solar_assistant']['username'] == "test_user"
        assert bot.config['webhook']['url'] == "https://webhook.example.com"
        assert bot.config['schedule']['interval_hours'] == 1

    def test_load_missing_config_raises_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError."""
        from solar_assistant_bot import SolarAssistantBot
        
        with pytest.raises(FileNotFoundError):
            SolarAssistantBot(config_path=str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises JSONDecodeError."""
        config_path = tmp_path / "invalid.json"
        with open(config_path, 'w') as f:
            f.write("{ invalid json }")
        
        from solar_assistant_bot import SolarAssistantBot
        
        with pytest.raises(json.JSONDecodeError):
            SolarAssistantBot(config_path=str(config_path))


class TestStatusDetection:
    """Tests for status detection functionality."""

    @pytest.fixture
    def bot_with_config(self, tmp_path):
        """Create a bot instance with a valid config."""
        config_data = {
            "solar_assistant": {
                "url": "https://example.com",
                "username": "test_user",
                "password": "test_pass"
            },
            "webhook": {
                "url": "https://webhook.example.com",
                "method": "POST",
                "headers": {}
            },
            "alerts": {
                "enabled": True,
                "webhook_url": "https://alerts.example.com",
                "check_for_offline": True,
                "min_alert_interval_minutes": 30
            },
            "schedule": {
                "interval_hours": 1,
                "enabled": True
            },
            "screenshot": {
                "wait_time_seconds": 10,
                "full_page": True,
                "quality": 90
            }
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        from solar_assistant_bot import SolarAssistantBot
        return SolarAssistantBot(config_path=str(config_path))

    def test_should_send_alert_on_grid_offline(self, bot_with_config):
        """Test that alert is sent when grid goes offline."""
        bot_with_config.last_system_status = "grid_online"
        
        result = bot_with_config.should_send_alert("grid_offline")
        
        assert result is True

    def test_should_send_alert_on_grid_recovery(self, bot_with_config):
        """Test that alert is sent when grid recovers."""
        bot_with_config.last_system_status = "grid_offline"
        
        result = bot_with_config.should_send_alert("grid_online")
        
        assert result is True

    def test_no_alert_when_status_unchanged(self, bot_with_config):
        """Test that no alert is sent when status is unchanged."""
        bot_with_config.last_system_status = "grid_online"
        
        result = bot_with_config.should_send_alert("grid_online")
        
        assert result is False


class TestSystemStatusPersistence:
    """Tests for system status file persistence."""

    @pytest.fixture
    def bot_with_temp_status(self, tmp_path):
        """Create a bot with temporary status file."""
        config_data = {
            "solar_assistant": {
                "url": "https://example.com",
                "username": "test_user",
                "password": "test_pass"
            },
            "webhook": {
                "url": "https://webhook.example.com",
                "method": "POST",
                "headers": {}
            },
            "alerts": {"enabled": True, "min_alert_interval_minutes": 30},
            "schedule": {"interval_hours": 1, "enabled": True},
            "screenshot": {"wait_time_seconds": 10, "full_page": True, "quality": 90}
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        from solar_assistant_bot import SolarAssistantBot
        bot = SolarAssistantBot(config_path=str(config_path))
        bot.status_file = str(tmp_path / "status.json")
        return bot

    def test_save_and_load_status(self, bot_with_temp_status):
        """Test saving and loading system status."""
        bot_with_temp_status.save_system_status("grid_offline")
        
        # Reset and reload
        bot_with_temp_status.last_system_status = None
        bot_with_temp_status.load_system_status()
        
        assert bot_with_temp_status.last_system_status == "grid_offline"

    def test_load_nonexistent_status_file(self, bot_with_temp_status):
        """Test loading when status file doesn't exist."""
        bot_with_temp_status.status_file = "/nonexistent/path/status.json"
        
        # Should not raise error
        bot_with_temp_status.load_system_status()
        
        assert bot_with_temp_status.last_system_status is None
