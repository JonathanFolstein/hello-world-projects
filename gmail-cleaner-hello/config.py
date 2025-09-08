"""
Configuration Management for Gmail Storage Manager

This module handles all configuration settings including user preferences,
filter settings, storage locations, and safety parameters.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class FilterConfig:
    """Email filtering configuration settings"""
    # Time-based filters
    older_than_days: int = 365  # Default: 1 year
    newer_than_days: Optional[int] = None
    
    # Size-based filters (in MB)
    min_size_mb: Optional[float] = None
    max_size_mb: Optional[float] = None
    large_attachment_mb: float = 10.0
    
    # Sender-based filters
    exclude_senders: list = None
    include_senders: list = None
    newsletter_domains: list = None
    
    # Content-based filters
    exclude_labels: list = None
    include_labels: list = None
    exclude_folders: list = None
    
    # Custom search queries
    custom_queries: list = None
    
    def __post_init__(self):
        """Initialize list fields to avoid mutable default arguments"""
        if self.exclude_senders is None:
            self.exclude_senders = []
        if self.include_senders is None:
            self.include_senders = []
        if self.newsletter_domains is None:
            self.newsletter_domains = [
                'noreply@', 'no-reply@', 'newsletter@', 'marketing@',
                'notifications@', 'updates@', 'support@'
            ]
        if self.exclude_labels is None:
            self.exclude_labels = ['IMPORTANT', 'STARRED']
        if self.include_labels is None:
            self.include_labels = []
        if self.exclude_folders is None:
            self.exclude_folders = ['SENT', 'DRAFTS']
        if self.custom_queries is None:
            self.custom_queries = []


@dataclass
class StorageConfig:
    """Local storage configuration settings"""
    base_path: str = "./gmail_archive"
    export_format: str = "mbox"  # Options: mbox, eml, json
    create_date_folders: bool = True
    compress_archives: bool = True
    encryption_enabled: bool = True
    max_file_size_mb: int = 100  # Max size per archive file
    
    
@dataclass
class SafetyConfig:
    """Safety and verification settings"""
    dry_run_mode: bool = True
    require_confirmation: bool = True
    backup_verification_level: str = "full"  # Options: none, basic, full
    soft_delete: bool = True  # Move to trash vs permanent delete
    batch_size: int = 50  # Emails processed per batch
    rate_limit_delay: float = 0.1  # Seconds between API calls
    max_retries: int = 3
    enable_rollback: bool = True
    

@dataclass
class AuthConfig:
    """Authentication configuration"""
    credentials_file: str = "credentials/client_secret.json"
    token_file: str = "credentials/token.json"
    scopes: list = None
    
    def __post_init__(self):
        """Initialize OAuth2 scopes for Gmail API"""
        if self.scopes is None:
            self.scopes = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify'
            ]


@dataclass
class LoggingConfig:
    """Logging and monitoring configuration"""
    log_level: str = "INFO"
    log_file: str = "logs/gmail_manager.log"
    audit_log: str = "logs/audit.log"
    enable_progress_bar: bool = True
    enable_rich_console: bool = True
    max_log_size_mb: int = 10
    log_retention_days: int = 30


class Config:
    """
    Main configuration class that manages all application settings.
    
    Supports loading from YAML/JSON files and provides default values
    for all configuration options.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration with optional config file.
        
        Args:
            config_file: Path to YAML or JSON configuration file
        """
        # Initialize with default configurations
        self.filter = FilterConfig()
        self.storage = StorageConfig()
        self.safety = SafetyConfig()
        self.auth = AuthConfig()
        self.logging = LoggingConfig()
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # Ensure required directories exist
        self._ensure_directories()
    
    def load_from_file(self, config_file: str) -> None:
        """
        Load configuration from YAML or JSON file.
        
        Args:
            config_file: Path to configuration file
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If config file doesn't exist
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        # Update configurations with loaded data
        if 'filter' in config_data:
            self._update_dataclass(self.filter, config_data['filter'])
        if 'storage' in config_data:
            self._update_dataclass(self.storage, config_data['storage'])
        if 'safety' in config_data:
            self._update_dataclass(self.safety, config_data['safety'])
        if 'auth' in config_data:
            self._update_dataclass(self.auth, config_data['auth'])
        if 'logging' in config_data:
            self._update_dataclass(self.logging, config_data['logging'])
    
    def save_to_file(self, config_file: str) -> None:
        """
        Save current configuration to YAML or JSON file.
        
        Args:
            config_file: Path to save configuration file
        """
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert all dataclasses to dictionaries
        config_data = {
            'filter': asdict(self.filter),
            'storage': asdict(self.storage),
            'safety': asdict(self.safety),
            'auth': asdict(self.auth),
            'logging': asdict(self.logging)
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            elif config_path.suffix.lower() == '.json':
                json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    def _update_dataclass(self, dataclass_instance: Any, update_dict: Dict[str, Any]) -> None:
        """
        Update dataclass fields with values from dictionary.
        
        Args:
            dataclass_instance: Dataclass instance to update
            update_dict: Dictionary with new values
        """
        for key, value in update_dict.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist"""
        directories = [
            Path(self.storage.base_path),
            Path(self.auth.credentials_file).parent,
            Path(self.logging.log_file).parent,
            Path(self.logging.audit_log).parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_filter_date_cutoff(self) -> datetime:
        """
        Calculate the date cutoff for email filtering.
        
        Returns:
            datetime: Cutoff date for filtering old emails
        """
        return datetime.now() - timedelta(days=self.filter.older_than_days)
    
    def validate(self) -> list:
        """
        Validate configuration settings and return any issues found.
        
        Returns:
            list: List of validation error messages
        """
        errors = []
        
        # Validate storage path
        storage_path = Path(self.storage.base_path)
        if not storage_path.parent.exists():
            errors.append(f"Storage parent directory doesn't exist: {storage_path.parent}")
        
        # Validate export format
        valid_formats = ['mbox', 'eml', 'json']
        if self.storage.export_format not in valid_formats:
            errors.append(f"Invalid export format: {self.storage.export_format}. Must be one of: {valid_formats}")
        
        # Validate batch size
        if self.safety.batch_size <= 0 or self.safety.batch_size > 1000:
            errors.append(f"Batch size must be between 1 and 1000: {self.safety.batch_size}")
        
        # Validate credentials file path
        creds_path = Path(self.auth.credentials_file)
        if not creds_path.parent.exists():
            errors.append(f"Credentials directory doesn't exist: {creds_path.parent}")
        
        return errors


def create_default_config_file(config_file: str = "config.yaml") -> None:
    """
    Create a default configuration file with all available options.
    
    Args:
        config_file: Path where to create the config file
    """
    config = Config()
    config.save_to_file(config_file)
    print(f"Default configuration file created: {config_file}")


if __name__ == "__main__":
    # Example usage and testing
    print("Gmail Storage Manager - Configuration System")
    print("=" * 50)
    
    # Create default config
    config = Config()
    
    # Display current settings
    print(f"Storage path: {config.storage.base_path}")
    print(f"Filter older than: {config.filter.older_than_days} days")
    print(f"Dry run mode: {config.safety.dry_run_mode}")
    print(f"Export format: {config.storage.export_format}")
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print(f"Configuration errors found: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    # Create example config file
    create_default_config_file("example_config.yaml")
