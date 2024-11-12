from typing import Dict, Any, Union, Optional
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValueCleaner:
    """Handles cleaning and conversion of monetary values."""
    
    @staticmethod
    def convert_currency(value: str) -> Optional[float]:
        """
        Convert currency strings to float values.
        Examples:
            "€5M" -> 5000000.0
            "€500K" -> 500000.0
            "€1,500" -> 1500.0
        """
        try:
            # Remove currency symbol and whitespace
            value = value.replace('€', '').replace(' ', '')
            
            # Handle millions
            if 'M' in value:
                value = float(value.replace('M', '')) * 1_000_000
            # Handle thousands
            elif 'K' in value:
                value = float(value.replace('K', '')) * 1_000
            else:
                # Remove commas and convert to float
                value = float(value.replace(',', ''))
                
            return value
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error converting currency value {value}: {e}")
            return None

    @staticmethod
    def format_currency(value: float, include_symbol: bool = True) -> str:
        """
        Format float values as currency strings.
        Examples:
            5000000.0 -> "€5M"
            500000.0 -> "€500K"
            1500.0 -> "€1,500"
        """
        symbol = '€' if include_symbol else ''
        
        if value >= 1_000_000:
            return f"{symbol}{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{symbol}{value/1_000:.0f}K"
        else:
            return f"{symbol}{value:,.0f}"

class DateCleaner:
    """Handles cleaning and validation of dates."""
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse various date formats.
        Handles formats like:
        - "2024"
        - "Jun 30, 2024"
        - "30/06/2024"
        - "2024-06-30"
        """
        date_formats = [
            "%Y",
            "%b %d, %Y",
            "%d/%m/%Y",
            "%Y-%m-%d"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def format_date(date: datetime, format_str: str = "%Y-%m-%d") -> str:
        """Format datetime object to string."""
        return date.strftime(format_str)

class AttributeCleaner:
    """Handles cleaning and standardization of player attributes."""
    
    @staticmethod
    def clean_name(name: str) -> str:
        """
        Clean and standardize player names.
        - Remove extra whitespace
        - Handle special characters
        - Standardize capitalization
        """
        if not name:
            return ""
            
        # Remove extra whitespace
        name = " ".join(name.split())
        
        # Handle special characters (like accents)
        # You might want to keep or transform them based on your needs
        name = name.encode('ascii', 'ignore').decode('ascii')
        
        # Capitalize each word
        return name.title()

    @staticmethod
    def clean_position(position: str) -> Optional[str]:
        """
        Clean and validate position strings.
        Examples: 
            "ST" -> "ST"
            "striker" -> "ST"
            "cf" -> "CF"
        """
        position_map = {
            "striker": "ST",
            "forward": "FW",
            "midfielder": "MF",
            "defender": "DF",
            "goalkeeper": "GK",
            # Add more mappings as needed
        }
        
        # Clean and standardize
        pos = position.strip().lower()
        
        # Check if it's already a valid abbreviation
        if len(pos) <= 3 and pos.isalpha():
            return pos.upper()
            
        # Try to map to standard abbreviation
        return position_map.get(pos)

def clean_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean player statistics dictionary.
    - Converts string numbers to integers/floats
    - Handles percentage values
    - Validates ranges
    """
    cleaned = {}
    
    for key, value in stats.items():
        try:
            # Handle percentage values
            if isinstance(value, str) and '%' in value:
                cleaned[key] = float(value.replace('%', '')) / 100
                continue
                
            # Try to convert to numeric
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point
                numeric_str = re.sub(r'[^\d.]', '', value)
                if '.' in numeric_str:
                    cleaned[key] = float(numeric_str)
                else:
                    cleaned[key] = int(numeric_str)
            else:
                cleaned[key] = value
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error cleaning stat {key}: {value} - {e}")
            cleaned[key] = value
            
    return cleaned

class DataValidator:
    """Validates cleaned data."""
    
    @staticmethod
    def validate_age(age: Union[int, str]) -> Optional[int]:
        """Validate player age is within reasonable range."""
        try:
            age_int = int(age)
            if 15 <= age_int <= 45:
                return age_int
            logger.warning(f"Age {age} outside valid range")
            return None
        except (ValueError, TypeError):
            logger.warning(f"Invalid age value: {age}")
            return None

    @staticmethod
    def validate_value(value: Union[float, str]) -> Optional[float]:
        """Validate monetary value is reasonable."""
        try:
            if isinstance(value, str):
                value = ValueCleaner.convert_currency(value)
            if value is None:
                return None
            if 0 <= value <= 500_000_000:  # Max 500M
                return value
            logger.warning(f"Value {value} outside valid range")
            return None
        except (ValueError, TypeError):
            logger.warning(f"Invalid monetary value: {value}")
            return None