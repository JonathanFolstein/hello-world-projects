"""
Gmail API Client for Gmail Storage Manager

This module handles Gmail API authentication, token management,
and provides methods for email operations following Google's best practices.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Generator
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.utils import parsedate_to_datetime

from config import Config


class GmailAPIError(Exception):
    """Custom exception for Gmail API related errors"""
    pass


class GmailClient:
    """
    Gmail API client that handles authentication and email operations.
    
    This client provides methods for:
    - OAuth2 authentication with token refresh
    - Email querying and filtering  
    - Email metadata retrieval
    - Email content downloading
    - Batch operations for efficiency
    - Rate limiting and error handling
    """
    
    def __init__(self, config: Config):
        """
        Initialize Gmail client with configuration.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.service = None
        self.credentials = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication
        self._authenticate()
    
    def _authenticate(self) -> None:
        """
        Handle OAuth2 authentication flow with token refresh.
        
        This method:
        1. Checks for existing valid tokens
        2. Refreshes expired tokens if possible
        3. Runs OAuth flow for new authentication
        4. Saves tokens for future use
        
        Raises:
            GmailAPIError: If authentication fails
        """
        creds = None
        token_path = Path(self.config.auth.token_file)
        
        # Load existing token if available
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    self.config.auth.token_file, 
                    self.config.auth.scopes
                )
                self.logger.info("Loaded existing authentication token")
            except Exception as e:
                self.logger.warning(f"Failed to load token file: {e}")
        
        # Refresh expired credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self.logger.info("Refreshed expired authentication token")
            except Exception as e:
                self.logger.warning(f"Failed to refresh token: {e}")
                creds = None
        
        # Run OAuth flow if no valid credentials
        if not creds or not creds.valid:
            credentials_path = Path(self.config.auth.credentials_file)
            if not credentials_path.exists():
                raise GmailAPIError(
                    f"Credentials file not found: {credentials_path}. "
                    "Please download your OAuth2 credentials from Google Cloud Console."
                )
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.auth.credentials_file,
                    self.config.auth.scopes
                )
                creds = flow.run_local_server(port=0)
                self.logger.info("Completed OAuth2 authentication flow")
            except Exception as e:
                raise GmailAPIError(f"OAuth2 authentication failed: {e}")
        
        # Save credentials for next run
        try:
            with open(self.config.auth.token_file, 'w') as token:
                token.write(creds.to_json())
            self.logger.info("Saved authentication token")
        except Exception as e:
            self.logger.warning(f"Failed to save token: {e}")
        
        # Build Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            self.logger.info("Successfully initialized Gmail API client")
        except Exception as e:
            raise GmailAPIError(f"Failed to build Gmail service: {e}")
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Get Gmail profile information.
        
        Returns:
            Dict containing profile information including email address and storage usage
            
        Raises:
            GmailAPIError: If API call fails
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            self.logger.info(f"Retrieved profile for: {profile.get('emailAddress')}")
            return profile
        except HttpError as e:
            raise GmailAPIError(f"Failed to get profile: {e}")
    
    def search_messages(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for messages using Gmail search query syntax.
        
        Args:
            query: Gmail search query (e.g., "older_than:1y")
            max_results: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with id and threadId
            
        Raises:
            GmailAPIError: If search fails
        """
        try:
            messages = []
            page_token = None
            
            while True:
                # Execute search request
                request = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token,
                    maxResults=min(500, max_results) if max_results else 500
                )
                
                response = request.execute()
                
                # Add messages from this page
                if 'messages' in response:
                    messages.extend(response['messages'])
                    
                    # Check if we've reached max_results
                    if max_results and len(messages) >= max_results:
                        messages = messages[:max_results]
                        break
                
                # Check for more pages
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            self.logger.info(f"Found {len(messages)} messages for query: {query}")
            return messages
            
        except HttpError as e:
            raise GmailAPIError(f"Message search failed: {e}")
    
    def get_message(self, message_id: str, format: str = 'full') -> Dict[str, Any]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Gmail message ID
            format: Message format ('minimal', 'full', 'raw', 'metadata')
            
        Returns:
            Message dictionary with headers, body, and attachments
            
        Raises:
            GmailAPIError: If message retrieval fails
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format=format
            ).execute()
            
            return message
            
        except HttpError as e:
            raise GmailAPIError(f"Failed to get message {message_id}: {e}")
    
    def get_messages_batch(self, message_ids: List[str], format: str = 'full') -> List[Dict[str, Any]]:
        """
        Get multiple messages efficiently using batch requests.
        
        Args:
            message_ids: List of Gmail message IDs
            format: Message format for all messages
            
        Returns:
            List of message dictionaries
            
        Raises:
            GmailAPIError: If batch request fails
        """
        if not message_ids:
            return []
        
        messages = []
        
        # Process in batches of 100 (Gmail API limit)
        batch_size = 100
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i + batch_size]
            
            try:
                batch_messages = []
                for msg_id in batch_ids:
                    message = self.get_message(msg_id, format)
                    batch_messages.append(message)
                
                messages.extend(batch_messages)
                self.logger.debug(f"Retrieved batch of {len(batch_messages)} messages")
                
            except Exception as e:
                self.logger.error(f"Batch request failed for IDs {batch_ids}: {e}")
                raise GmailAPIError(f"Batch message retrieval failed: {e}")
        
        self.logger.info(f"Retrieved {len(messages)} messages in total")
        return messages
    
    def delete_message(self, message_id: str, permanent: bool = False) -> bool:
        """
        Delete a message (move to trash or permanently delete).
        
        Args:
            message_id: Gmail message ID to delete
            permanent: If True, permanently delete; if False, move to trash
            
        Returns:
            True if deletion successful
            
        Raises:
            GmailAPIError: If deletion fails
        """
        try:
            if permanent:
                # Permanently delete the message
                self.service.users().messages().delete(
                    userId='me',
                    id=message_id
                ).execute()
                self.logger.debug(f"Permanently deleted message: {message_id}")
            else:
                # Move to trash
                self.service.users().messages().trash(
                    userId='me',
                    id=message_id
                ).execute()
                self.logger.debug(f"Moved to trash: {message_id}")
            
            return True
            
        except HttpError as e:
            error_msg = f"Failed to delete message {message_id}: {e}"
            self.logger.error(error_msg)
            raise GmailAPIError(error_msg)
    
    def delete_messages_batch(self, message_ids: List[str], permanent: bool = False) -> Dict[str, List[str]]:
        """
        Delete multiple messages efficiently.
        
        Args:
            message_ids: List of message IDs to delete
            permanent: If True, permanently delete; if False, move to trash
            
        Returns:
            Dictionary with 'success' and 'failed' lists of message IDs
            
        Raises:
            GmailAPIError: If batch deletion fails completely
        """
        if not message_ids:
            return {'success': [], 'failed': []}
        
        success_ids = []
        failed_ids = []
        
        # Process deletions individually to handle partial failures
        for message_id in message_ids:
            try:
                self.delete_message(message_id, permanent)
                success_ids.append(message_id)
            except GmailAPIError:
                failed_ids.append(message_id)
                continue
        
        self.logger.info(
            f"Batch deletion completed: {len(success_ids)} successful, "
            f"{len(failed_ids)} failed"
        )
        
        return {'success': success_ids, 'failed': failed_ids}
    
    def extract_message_metadata(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract useful metadata from a Gmail message object.
        
        Args:
            message: Gmail message dictionary
            
        Returns:
            Dictionary with extracted metadata (date, from, subject, size, etc.)
        """
        metadata = {
            'id': message.get('id'),
            'thread_id': message.get('threadId'),
            'label_ids': message.get('labelIds', []),
            'size_estimate': message.get('sizeEstimate', 0),
        }
        
        # Extract headers
        headers = {}
        payload = message.get('payload', {})
        for header in payload.get('headers', []):
            headers[header['name'].lower()] = header['value']
        
        # Common header fields
        metadata.update({
            'subject': headers.get('subject', ''),
            'from': headers.get('from', ''),
            'to': headers.get('to', ''),
            'date_str': headers.get('date', ''),
            'message_id_header': headers.get('message-id', ''),
        })
        
        # Parse date
        try:
            if metadata['date_str']:
                metadata['date'] = parsedate_to_datetime(metadata['date_str'])
            else:
                metadata['date'] = None
        except Exception:
            metadata['date'] = None
        
        # Check for attachments
        metadata['has_attachments'] = self._has_attachments(payload)
        metadata['attachment_count'] = self._count_attachments(payload)
        
        return metadata
    
    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """
        Check if message has attachments.
        
        Args:
            payload: Message payload from Gmail API
            
        Returns:
            True if message has attachments
        """
        parts = payload.get('parts', [])
        if not parts:
            return False
        
        for part in parts:
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                return True
            # Check nested parts
            if self._has_attachments(part):
                return True
        
        return False
    
    def _count_attachments(self, payload: Dict[str, Any]) -> int:
        """
        Count number of attachments in message.
        
        Args:
            payload: Message payload from Gmail API
            
        Returns:
            Number of attachments
        """
        count = 0
        parts = payload.get('parts', [])
        
        for part in parts:
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                count += 1
            # Count nested parts
            count += self._count_attachments(part)
        
        return count
    
    def get_storage_usage(self) -> Dict[str, int]:
        """
        Get current Gmail storage usage information.
        
        Returns:
            Dictionary with storage usage statistics
            
        Raises:
            GmailAPIError: If unable to retrieve storage info
        """
        try:
            profile = self.get_profile()
            
            # Extract storage info from profile
            usage_info = {
                'total_size_estimate': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0),
                'history_id': profile.get('historyId', ''),
            }
            
            # Get quota usage (this requires additional API call)
            # Note: Actual quota info requires Drive API access
            
            return usage_info
            
        except Exception as e:
            raise GmailAPIError(f"Failed to get storage usage: {e}")


if __name__ == "__main__":
    # Example usage and testing
    from config import Config
    
    print("Gmail API Client - Testing")
    print("=" * 30)
    
    try:
        # Initialize with default config
        config = Config()
        client = GmailClient(config)
        
        # Get profile info
        profile = client.get_profile()
        print(f"Authenticated as: {profile.get('emailAddress')}")
        print(f"Total messages: {profile.get('messagesTotal', 'Unknown')}")
        
        # Test search (limit to 5 messages to avoid overwhelming output)
        print("\nSearching for recent messages...")
        messages = client.search_messages("newer_than:7d", max_results=5)
        print(f"Found {len(messages)} recent messages")
        
        # Get metadata for first message
        if messages:
            first_msg = client.get_message(messages[0]['id'], format='metadata')
            metadata = client.extract_message_metadata(first_msg)
            print(f"\nFirst message metadata:")
            print(f"  Subject: {metadata['subject'][:50]}...")
            print(f"  From: {metadata['from'][:50]}...")
            print(f"  Date: {metadata['date']}")
            print(f"  Size: {metadata['size_estimate']} bytes")
            print(f"  Has attachments: {metadata['has_attachments']}")
        
    except GmailAPIError as e:
        print(f"Gmail API Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
