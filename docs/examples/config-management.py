#!/usr/bin/env python3
"""
Configuration Management Example - Simplified Implementation
Demonstrates configuration loading, validation, and hot-reloading concepts

Note: This is a simplified educational example created for demo purposes.
"""

import json
import os
import time
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationError:
    """Represents a configuration validation error"""
    field: str
    message: str
    severity: str  # 'error', 'warning'


class ConfigSchema:
    """
    Simplified configuration schema validator.
    Demonstrates validation concepts without external dependencies.
    """

    def __init__(self):
        self.required_fields = {
            'app': ['name', 'version'],
            'window': ['layout_mode', 'grid'],
            'ai_apps': []  # List validation handled separately
        }

        self.field_types = {
            'app.name': str,
            'app.version': str,
            'window.layout_mode': str,
            'window.grid.cols': int,
            'window.grid.rows': int
        }

        self.valid_values = {
            'window.layout_mode': ['grid', 'side_by_side']
        }

    def validate(self, config: Dict) -> Tuple[bool, List[ValidationError]]:
        """Validate configuration against schema"""
        errors = []

        # Check required sections
        for section in self.required_fields:
            if section not in config:
                errors.append(ValidationError(
                    field=section,
                    message=f"Required section '{section}' is missing",
                    severity='error'
                ))
                continue

            # Check required fields in section
            for field in self.required_fields[section]:
                if field not in config[section]:
                    errors.append(ValidationError(
                        field=f"{section}.{field}",
                        message=f"Required field '{field}' is missing",
                        severity='error'
                    ))

        # Type validation
        for field_path, expected_type in self.field_types.items():
            value = self._get_nested_value(config, field_path)
            if value is not None and not isinstance(value, expected_type):
                errors.append(ValidationError(
                    field=field_path,
                    message=f"Expected {expected_type.__name__}, got {type(value).__name__}",
                    severity='error'
                ))

        # Value validation
        for field_path, valid_options in self.valid_values.items():
            value = self._get_nested_value(config, field_path)
            if value is not None and value not in valid_options:
                errors.append(ValidationError(
                    field=field_path,
                    message=f"Invalid value '{value}'. Valid options: {valid_options}",
                    severity='error'
                ))

        # AI apps validation
        if 'ai_apps' in config:
            ai_errors = self._validate_ai_apps(config['ai_apps'])
            errors.extend(ai_errors)

        is_valid = not any(error.severity == 'error' for error in errors)
        return is_valid, errors

    def _get_nested_value(self, config: Dict, field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _validate_ai_apps(self, ai_apps: List[Dict]) -> List[ValidationError]:
        """Validate AI applications configuration"""
        errors = []

        if not isinstance(ai_apps, list):
            errors.append(ValidationError(
                field="ai_apps",
                message="AI apps must be a list",
                severity='error'
            ))
            return errors

        required_fields = ['name', 'enabled', 'priority']
        for i, app in enumerate(ai_apps):
            for field in required_fields:
                if field not in app:
                    errors.append(ValidationError(
                        field=f"ai_apps[{i}].{field}",
                        message=f"Required field '{field}' is missing",
                        severity='error'
                    ))

            # Validate priority is a positive integer
            if 'priority' in app:
                if not isinstance(app['priority'], int) or app['priority'] < 1:
                    errors.append(ValidationError(
                        field=f"ai_apps[{i}].priority",
                        message="Priority must be a positive integer",
                        severity='error'
                    ))

        return errors


class ConfigManager:
    """
    Simplified configuration management system.
    Demonstrates loading, validation, and hot-reloading concepts.
    """

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.schema = ConfigSchema()
        self.config = {}
        self.file_timestamps = {}
        self.observers = []

    def load_configuration(self) -> Tuple[bool, Optional[Dict], List[ValidationError]]:
        """Load and validate configuration from files"""
        errors = []

        # Load main settings
        settings_path = self.config_dir / "settings.json"
        if not settings_path.exists():
            errors.append(ValidationError(
                field="settings",
                message=f"Settings file not found: {settings_path}",
                severity='error'
            ))
            return False, None, errors

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception as e:
            errors.append(ValidationError(
                field="settings",
                message=f"Failed to parse settings file: {e}",
                severity='error'
            ))
            return False, None, errors

        # Load AI apps configuration
        ai_apps_path = self.config_dir / "ai_apps.json"
        if not ai_apps_path.exists():
            errors.append(ValidationError(
                field="ai_apps",
                message=f"AI apps file not found: {ai_apps_path}",
                severity='error'
            ))
            return False, None, errors

        try:
            with open(ai_apps_path, 'r', encoding='utf-8') as f:
                ai_apps_config = json.load(f)
                settings['ai_apps'] = ai_apps_config.get('ai_apps', [])
        except Exception as e:
            errors.append(ValidationError(
                field="ai_apps",
                message=f"Failed to parse AI apps file: {e}",
                severity='error'
            ))
            return False, None, errors

        # Validate configuration
        is_valid, validation_errors = self.schema.validate(settings)
        errors.extend(validation_errors)

        if is_valid:
            self.config = settings
            self._update_file_timestamps()
            self._notify_observers('config_loaded', self.config)

        return is_valid, settings, errors

    def save_configuration(self, config: Dict) -> Tuple[bool, List[ValidationError]]:
        """Save configuration with validation"""
        # Validate before saving
        is_valid, errors = self.schema.validate(config)
        if not is_valid:
            return False, errors

        try:
            # Split configuration for saving
            settings = {k: v for k, v in config.items() if k != 'ai_apps'}
            ai_apps = {'ai_apps': config.get('ai_apps', [])}

            # Save settings
            settings_path = self.config_dir / "settings.json"
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # Save AI apps
            ai_apps_path = self.config_dir / "ai_apps.json"
            with open(ai_apps_path, 'w', encoding='utf-8') as f:
                json.dump(ai_apps, f, indent=2, ensure_ascii=False)

            self.config = config
            self._update_file_timestamps()
            self._notify_observers('config_saved', self.config)

            return True, []

        except Exception as e:
            error = ValidationError(
                field="file_system",
                message=f"Failed to save configuration: {e}",
                severity='error'
            )
            return False, [error]

    def watch_for_changes(self) -> bool:
        """
        Check for configuration file changes.
        In a real implementation, this would use a file system watcher.
        """
        changes_detected = False

        for filename in ['settings.json', 'ai_apps.json']:
            file_path = self.config_dir / filename
            if file_path.exists():
                current_mtime = file_path.stat().st_mtime
                last_mtime = self.file_timestamps.get(filename, 0)

                if current_mtime > last_mtime:
                    changes_detected = True
                    break

        if changes_detected:
            # Reload configuration
            is_valid, new_config, errors = self.load_configuration()
            if is_valid:
                self._notify_observers('config_reloaded', new_config)
                return True
            else:
                self._notify_observers('config_error', errors)

        return changes_detected

    def add_observer(self, callback):
        """Add configuration change observer"""
        self.observers.append(callback)

    def remove_observer(self, callback):
        """Remove configuration change observer"""
        if callback in self.observers:
            self.observers.remove(callback)

    def _update_file_timestamps(self):
        """Update stored file modification timestamps"""
        for filename in ['settings.json', 'ai_apps.json']:
            file_path = self.config_dir / filename
            if file_path.exists():
                self.file_timestamps[filename] = file_path.stat().st_mtime

    def _notify_observers(self, event_type: str, data: Any):
        """Notify all observers of configuration changes"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                print(f"Observer notification failed: {e}")


def create_demo_config():
    """Create demo configuration files for testing"""
    config_dir = Path("demo_config")
    config_dir.mkdir(exist_ok=True)

    # Demo settings
    settings = {
        "app": {
            "name": "Multi-AI Chat Manager Demo",
            "version": "0.0.1"
        },
        "window": {
            "layout_mode": "grid",
            "grid": {
                "cols": 4,
                "rows": 2
            },
            "display": {
                "preferred_display": "auto"
            }
        },
        "gui": {
            "theme": "dark",
            "auto_arrange_on_startup": True
        }
    }

    # Demo AI apps
    ai_apps = {
        "ai_apps": [
            {
                "name": "AI Service A",
                "enabled": True,
                "priority": 1,
                "keywords": ["ai-service-a.com", "chat assistant a"]
            },
            {
                "name": "AI Service B",
                "enabled": True,
                "priority": 2,
                "keywords": ["ai-service-b.ai", "assistant chat b"]
            },
            {
                "name": "AI Service C",
                "enabled": True,
                "priority": 3,
                "keywords": ["ai-service-c.com", "chat helper c"]
            }
        ]
    }

    # Save files
    with open(config_dir / "settings.json", 'w') as f:
        json.dump(settings, f, indent=2)

    with open(config_dir / "ai_apps.json", 'w') as f:
        json.dump(ai_apps, f, indent=2)

    return str(config_dir)


def demo_usage():
    """Demonstrate configuration management usage"""
    print("Configuration Management Demo")
    print("=" * 40)

    # Create demo configuration
    config_dir = create_demo_config()
    print(f"Created demo config in: {config_dir}")

    # Create config manager
    config_manager = ConfigManager(config_dir)

    # Add observer
    def config_observer(event_type: str, data: Any):
        print(f"Config event: {event_type}")
        if event_type == 'config_error':
            for error in data:
                print(f"  Error: {error.field} - {error.message}")

    config_manager.add_observer(config_observer)

    # Load configuration
    print("\nLoading configuration...")
    is_valid, config, errors = config_manager.load_configuration()

    if is_valid:
        print("✓ Configuration loaded successfully")
        print(f"  App: {config['app']['name']} v{config['app']['version']}")
        print(f"  Layout: {config['window']['layout_mode']}")
        print(f"  AI Apps: {len(config['ai_apps'])} configured")
    else:
        print("✗ Configuration validation failed:")
        for error in errors:
            print(f"  {error.severity.upper()}: {error.field} - {error.message}")

    # Demonstrate validation
    print("\nTesting validation with invalid config...")
    invalid_config = config.copy()
    invalid_config['window']['layout_mode'] = 'invalid_mode'
    invalid_config['window']['grid']['cols'] = 'not_a_number'

    is_valid, errors = config_manager.schema.validate(invalid_config)
    print(f"Validation result: {'Valid' if is_valid else 'Invalid'}")
    for error in errors:
        print(f"  {error.severity.upper()}: {error.field} - {error.message}")

    # Demonstrate hot reloading
    print("\nTesting hot reload...")
    print("Checking for file changes...")
    changes = config_manager.watch_for_changes()
    print(f"Changes detected: {changes}")

    # Simulate file modification
    time.sleep(0.1)
    settings_path = Path(config_dir) / "settings.json"
    settings_path.touch()  # Update modification time

    print("File modified, checking again...")
    changes = config_manager.watch_for_changes()
    print(f"Changes detected: {changes}")


if __name__ == "__main__":
    demo_usage()