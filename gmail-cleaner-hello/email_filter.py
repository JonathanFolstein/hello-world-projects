"""
Email Filtering Engine for Gmail Storage Manager

This module provides intelligent filtering capabilities for emails based on
various criteria like date, size, sender, content, and custom rules.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from email.utils import parseaddr

from config import FilterConfig


@dataclass
class FilterResult:
    """Result of filtering operation with metadata"""
    should_process: bool
    reason: str
    confidence: float  # 0.0 to 1.0
    filter_type: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EmailFilter:
    """
    Advanced email filtering engine that applies multiple filtering criteria.
    
    This filter supports:
    - Time-based filtering (older than, newer than)
    - Size-based filtering (message size, attachment size)
    - Sender-based filtering (domains, specific addresses)
    - Content-based filtering (labels, folders, keywords)
    - Custom Gmail search queries
    - Smart categorization (newsletters, promotions, etc.)
    """
    
    def __init__(self, config: FilterConfig):
        """
        Initialize email filter with configuration.
        
        Args:
            config: Filter configuration settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for email filtering"""
        # Newsletter/marketing patterns
        self.newsletter_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in [
                r'unsubscribe',
                r'newsletter',
                r'marketing',
                r'promotional?',
                r'offer',
                r'deal',
                r'sale',
                r'discount',
                r'click here',
                r'limited time',
            ]
        ]
        
        # Automated email patterns
        self.automated_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r'noreply',
                r'no-reply',
                r'donotreply',
                r'automated',
                r'notification',
                r'alert',
                r'system',
            ]
        ]
    
    def should_process_email(self, email_metadata: Dict[str, Any]) -> FilterResult:
        """
        Determine if an email should be processed for archival/deletion.
        
        Args:
            email_metadata: Email metadata from Gmail API
            
        Returns:
            FilterResult indicating whether to process this email
        """
        # Apply filters in order of importance
        filters = [
            self._check_exclusions,
            self._check_time_filters,
            self._check_size_filters,
            self._check_sender_filters,
            self._check_content_filters,
            self._check_custom_queries,
        ]
        
        for filter_func in filters:
            result = filter_func(email_metadata)
            if result and not result.should_process:
                # Email excluded by this filter
                return result
        
        # If no filters excluded it, include it for processing
        return FilterResult(
            should_process=True,
            reason="Passed all filter criteria",
            confidence=0.8,
            filter_type="inclusive",
            metadata={'passed_all_filters': True}
        )
    
    def _check_exclusions(self, metadata: Dict[str, Any]) -> Optional[FilterResult]:
        """
        Check if email should be excluded based on protection rules.
        
        Args:
            metadata: Email metadata
            
        Returns:
            FilterResult if email should be excluded, None otherwise
        """
        # Check for important labels
        label_ids = metadata.get('label_ids', [])
        for exclude_label in self.config.exclude_labels:
            if exclude_label in label_ids:
                return FilterResult(
                    should_process=False,
                    reason=f"Has excluded label: {exclude_label}",
                    confidence=1.0,
                    filter_type="exclusion",
                    metadata={'excluded_label': exclude_label}
                )
        
        # Check for excluded folders
        for exclude_folder in self.config.exclude_folders:
            if exclude_folder in label_ids:
                return FilterResult(
                    should_process=False,
                    reason=f"In excluded folder: {exclude_folder}",
                    confidence=1.0,
                    filter_type="exclusion",
                    metadata={'excluded_folder': exclude_folder}
                )
        
        # Check for excluded senders
        sender = metadata.get('from', '').lower()
        for exclude_sender in self.config.exclude_senders:
            if exclude_sender.lower() in sender:
                return FilterResult(
                    should_process=False,
                    reason=f"From excluded sender: {exclude_sender}",
                    confidence=1.0,
                    filter_type="exclusion",
                    metadata={'excluded_sender': exclude_sender}
                )
        
        return None
    
    def _check_time_filters(self, metadata: Dict[str, Any]) -> Optional[FilterResult]:
        """
        Apply time-based filtering criteria.
        
        Args:
            metadata: Email metadata
            
        Returns:
            FilterResult if time criteria not met, None otherwise
        """
        email_date = metadata.get('date')
        if not email_date:
            # If we can't parse the date, be conservative
            return FilterResult(
                should_process=False,
                reason="Unable to parse email date",
                confidence=0.5,
                filter_type="time",
                metadata={'date_parse_error': True}
            )
        
        now = datetime.now(email_date.tzinfo) if email_date.tzinfo else datetime.now()
        
        # Check older_than filter
        if self.config.older_than_days:
            cutoff_date = now - timedelta(days=self.config.older_than_days)
            if email_date > cutoff_date:
                return FilterResult(
                    should_process=False,
                    reason=f"Email too recent (newer than {self.config.older_than_days} days)",
                    confidence=1.0,
                    filter_type="time",
                    metadata={
                        'email_age_days': (now - email_date).days,
                        'cutoff_days': self.config.older_than_days
                    }
                )
        
        # Check newer_than filter (if set)
        if self.config.newer_than_days:
            cutoff_date = now - timedelta(days=self.config.newer_than_days)
            if email_date < cutoff_date:
                return FilterResult(
                    should_process=False,
                    reason=f"Email too old (older than {self.config.newer_than_days} days)",
                    confidence=1.0,
                    filter_type="time",
                    metadata={
                        'email_age_days': (now - email_date).days,
                        'min_age_days': self.config.newer_than_days
                    }
                )
        
        return None
    
    def _check_size_filters(self, metadata: Dict[str, Any]) -> Optional[FilterResult]:
        """
        Apply size-based filtering criteria.
        
        Args:
            metadata: Email metadata
            
        Returns:
            FilterResult if size criteria not met, None otherwise
        """
        size_bytes = metadata.get('size_estimate', 0)
        size_mb = size_bytes / (1024 * 1024) if size_bytes else 0
        
        # Check minimum size filter
        if self.config.min_size_mb and size_mb < self.config.min_size_mb:
            return FilterResult(
                should_process=False,
                reason=f"Email too small ({size_mb:.2f} MB < {self.config.min_size_mb} MB)",
                confidence=0.8,
                filter_type="size",
                metadata={'size_mb': size_mb, 'min_size_mb': self.config.min_size_mb}
            )
        
        # Check maximum size filter
        if self.config.max_size_mb and size_mb > self.config.max_size_mb:
            return FilterResult(
                should_process=False,
                reason=f"Email too large ({size_mb:.2f} MB > {self.config.max_size_mb} MB)",
                confidence=0.8,
                filter_type="size",
                metadata={'size_mb': size_mb, 'max_size_mb': self.config.max_size_mb}
            )
        
        return None
    
    def _check_sender_filters(self, metadata: Dict[str, Any]) -> Optional[FilterResult]:
        """
        Apply sender-based filtering criteria.
        
        Args:
            metadata: Email metadata
            
        Returns:
            FilterResult if sender criteria not met, None otherwise
        """
        sender = metadata.get('from', '').lower()
        sender_email = parseaddr(sender)[1].lower()
        
        # Check include_senders filter (whitelist)
        if self.config.include_senders:
            included = False
            for include_sender in self.config.include_senders:
                if include_sender.lower() in sender:
                    included = True
                    break
            
            if not included:
                return FilterResult(
                    should_process=False,
                    reason="Sender not in whitelist",
                    confidence=0.9,
                    filter_type="sender",
                    metadata={'sender': sender_email, 'whitelist_only': True}
                )
        
        return None
    
    def _check_content_filters(self, metadata: Dict[str, Any]) -> Optional[FilterResult]:
        """
        Apply content-based filtering criteria.
        
        Args:
            metadata: Email metadata
            
        Returns:
            FilterResult if content criteria not met, None otherwise
        """
        # Check required labels (if any)
        if self.config.include_labels:
            label_ids = metadata.get('label_ids', [])
            has_required_label = any(
                label in label_ids for label in self.config.include_labels
            )
            
            if not has_required_label:
                return FilterResult(
                    should_process=False,
                    reason="Missing required labels",
                    confidence=0.8,
                    filter_type="content",
                    metadata={
                        'required_labels': self.config.include_labels,
                        'email_labels': label_ids
                    }
                )
        
        return None
    
    def _check_custom_queries(self, metadata: Dict[str, Any]) -> Optional[FilterResult]:
        """
        Apply custom Gmail search query filters.
        
        Note: This is a simplified version. Full implementation would require
        parsing Gmail search syntax and applying it to metadata.
        
        Args:
            metadata: Email metadata
            
        Returns:
            FilterResult if custom criteria not met, None otherwise
        """
        # For now, this is a placeholder for custom query logic
        # In a full implementation, you'd parse Gmail search queries
        # and apply them to the email metadata
        
        return None
    
    def categorize_email(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize email based on content analysis.
        
        Args:
            metadata: Email metadata
            
        Returns:
            Dictionary with categorization results
        """
        subject = metadata.get('subject', '').lower()
        sender = metadata.get('from', '').lower()
        sender_email = parseaddr(sender)[1].lower()
        
        categories = {
            'is_newsletter': False,
            'is_promotional': False,
            'is_automated': False,
            'is_social': False,
            'is_receipt': False,
            'confidence_scores': {}
        }
        
        # Newsletter detection
        newsletter_score = 0.0
        for pattern in self.newsletter_patterns:
            if pattern.search(subject):
                newsletter_score += 0.3
        
        # Check sender domain patterns
        for domain_pattern in self.config.newsletter_domains:
            if domain_pattern in sender_email:
                newsletter_score += 0.4
        
        categories['is_newsletter'] = newsletter_score > 0.5
        categories['confidence_scores']['newsletter'] = min(newsletter_score, 1.0)
        
        # Automated email detection
        automated_score = 0.0
        for pattern in self.automated_patterns:
            if pattern.search(sender_email):
                automated_score += 0.5
            if pattern.search(subject):
                automated_score += 0.3
        
        categories['is_automated'] = automated_score > 0.5
        categories['confidence_scores']['automated'] = min(automated_score, 1.0)
        
        # Promotional email detection
        promotional_keywords = ['sale', 'deal', 'offer', 'discount', 'limited time', '%']
        promotional_score = sum(0.2 for keyword in promotional_keywords if keyword in subject)
        
        categories['is_promotional'] = promotional_score > 0.4
        categories['confidence_scores']['promotional'] = min(promotional_score, 1.0)
        
        # Receipt detection
        receipt_keywords = ['receipt', 'invoice', 'payment', 'order', 'purchase', 'transaction']
        receipt_score = sum(0.3 for keyword in receipt_keywords if keyword in subject)
        
        categories['is_receipt'] = receipt_score > 0.6
        categories['confidence_scores']['receipt'] = min(receipt_score, 1.0)
        
        return categories
    
    def build_gmail_query(self) -> str:
        """
        Build Gmail search query string based on current filter configuration.
        
        Returns:
            Gmail search query string
        """
        query_parts = []
        
        # Time-based filters
        if self.config.older_than_days:
            query_parts.append(f"older_than:{self.config.older_than_days}d")
        
        if self.config.newer_than_days:
            query_parts.append(f"newer_than:{self.config.newer_than_days}d")
        
        # Size-based filters
        if self.config.min_size_mb:
            size_bytes = int(self.config.min_size_mb * 1024 * 1024)
            query_parts.append(f"larger:{size_bytes}")
        
        if self.config.max_size_mb:
            size_bytes = int(self.config.max_size_mb * 1024 * 1024)
            query_parts.append(f"smaller:{size_bytes}")
        
        # Exclude important labels
        for label in self.config.exclude_labels:
            query_parts.append(f"-label:{label}")
        
        # Exclude folders
        for folder in self.config.exclude_folders:
            query_parts.append(f"-in:{folder}")
        
        # Include specific labels
        if self.config.include_labels:
            label_parts = [f"label:{label}" for label in self.config.include_labels]
            query_parts.append(f"({' OR '.join(label_parts)})")
        
        # Sender filters
        if self.config.exclude_senders:
            for sender in self.config.exclude_senders:
                query_parts.append(f"-from:{sender}")
        
        if self.config.include_senders:
            sender_parts = [f"from:{sender}" for sender in self.config.include_senders]
            query_parts.append(f"({' OR '.join(sender_parts)})")
        
        # Custom queries
        query_parts.extend(self.config.custom_queries)
        
        # Join all parts with AND logic
        return ' '.join(query_parts)
    
    def get_filter_stats(self, emails_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics about filtering results.
        
        Args:
            emails_metadata: List of email metadata to analyze
            
        Returns:
            Dictionary with filtering statistics
        """
        stats = {
            'total_emails': len(emails_metadata),
            'would_process': 0,
            'excluded_by_filter': {},
            'categories': {
                'newsletter': 0,
                'promotional': 0,
                'automated': 0,
                'receipt': 0,
                'social': 0
            },
            'size_distribution': {'small': 0, 'medium': 0, 'large': 0},
            'age_distribution': {'recent': 0, 'medium': 0, 'old': 0}
        }
        
        for metadata in emails_metadata:
            # Check if would be processed
            result = self.should_process_email(metadata)
            if result.should_process:
                stats['would_process'] += 1
            else:
                filter_type = result.filter_type
                stats['excluded_by_filter'][filter_type] = stats['excluded_by_filter'].get(filter_type, 0) + 1
            
            # Categorize email
            categories = self.categorize_email(metadata)
            for cat_name, is_category in categories.items():
                if cat_name.startswith('is_') and is_category:
                    cat_key = cat_name[3:]  # Remove 'is_' prefix
                    if cat_key in stats['categories']:
                        stats['categories'][cat_key] += 1
            
            # Size distribution
            size_mb = metadata.get('size_estimate', 0) / (1024 * 1024)
            if size_mb < 1:
                stats['size_distribution']['small'] += 1
            elif size_mb < 10:
                stats['size_distribution']['medium'] += 1
            else:
                stats['size_distribution']['large'] += 1
            
            # Age distribution
            if metadata.get('date'):
                age_days = (datetime.now() - metadata['date']).days
                if age_days < 30:
                    stats['age_distribution']['recent'] += 1
                elif age_days < 365:
                    stats['age_distribution']['medium'] += 1
                else:
                    stats['age_distribution']['old'] += 1
        
        # Calculate percentages
        if stats['total_emails'] > 0:
            stats['process_percentage'] = (stats['would_process'] / stats['total_emails']) * 100
        else:
            stats['process_percentage'] = 0
        
        return stats


if __name__ == "__main__":
    # Example usage and testing
    from config import Config
    
    print("Email Filter - Testing")
    print("=" * 30)
    
    # Create test configuration
    config = Config()
    email_filter = EmailFilter(config.filter)
    
    # Test email metadata
    test_emails = [
        {
            'id': '1',
            'subject': 'Newsletter: Weekly Updates',
            'from': 'newsletter@example.com',
            'date': datetime.now() - timedelta(days=400),
            'size_estimate': 50000,
            'label_ids': ['INBOX'],
        },
        {
            'id': '2', 
            'subject': 'Important Meeting Tomorrow',
            'from': 'boss@company.com',
            'date': datetime.now() - timedelta(days=10),
            'size_estimate': 25000,
            'label_ids': ['INBOX', 'IMPORTANT'],
        },
        {
            'id': '3',
            'subject': 'Special Offer - 50% Off!',
            'from': 'sales@retailer.com',
            'date': datetime.now() - timedelta(days=500),
            'size_estimate': 75000,
            'label_ids': ['INBOX', 'PROMOTIONS'],
        }
    ]
    
    print("Testing individual emails:")
    for email in test_emails:
        result = email_filter.should_process_email(email)
        categories = email_filter.categorize_email(email)
        
        print(f"\nEmail: {email['subject'][:30]}...")
        print(f"  Should process: {result.should_process}")
        print(f"  Reason: {result.reason}")
        print(f"  Categories: {[k for k,v in categories.items() if k.startswith('is_') and v]}")
    
    # Test Gmail query building
    print(f"\nGenerated Gmail Query:")
    print(email_filter.build_gmail_query())
    
    # Test statistics
    stats = email_filter.get_filter_stats(test_emails)
    print(f"\nFilter Statistics:")
    print(f"  Total emails: {stats['total_emails']}")
    print(f"  Would process: {stats['would_process']} ({stats['process_percentage']:.1f}%)")
    print(f"  Exclusions: {stats['excluded_by_filter']}")
    print(f"  Categories: {stats['categories']}")
