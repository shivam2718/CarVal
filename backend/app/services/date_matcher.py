"""
Smart date matching for document verification
Handles various date formats and month representations
"""

import re
from datetime import datetime
from typing import Tuple, Optional

class DateMatcher:
    """Matches dates in various formats and month representations"""
    
    # Month mappings
    MONTH_NAMES = {
        'january': '01', 'jan': '01', 'january': '01',
        'february': '02', 'feb': '02',
        'march': '03', 'mar': '03',
        'april': '04', 'apr': '04',
        'may': '05',
        'june': '06', 'jun': '06',
        'july': '07', 'jul': '07',
        'august': '08', 'aug': '08',
        'september': '09', 'sep': '09', 'sept': '09',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12',
    }
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[Tuple[str, str, str]]:
        """
        Normalize a date string to (day, month, year) format
        Handles: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, DD MON YYYY, etc.
        
        Returns: (day, month, year) as 2-digit/4-digit strings or None if not parseable
        """
        if not date_str or date_str.strip() == "":
            return None
        
        date_str = date_str.strip().lower()
        
        # Try ISO format: YYYY-MM-DD
        match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if match:
            year, month, day = match.groups()
            return (day, month, year)
        
        # Try YYYY/MM/DD
        match = re.match(r'(\d{4})/(\d{2})/(\d{2})', date_str)
        if match:
            year, month, day = match.groups()
            return (day, month, year)
        
        # Try DD-MM-YYYY or DD/MM/YYYY
        match = re.match(r'(\d{2})[-/](\d{2})[-/](\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            return (day, month, year)
        
        # Try DD-MM-YY or DD/MM/YY (assume 20xx for recent years)
        match = re.match(r'(\d{2})[-/](\d{2})[-/](\d{2})', date_str)
        if match:
            day, month, year = match.groups()
            year_int = int(year)
            year = f"20{year}" if year_int < 100 else str(year_int)
            return (day, month, year)
        
        # Try month name format: DD-JAN-YYYY or JAN-DD-YYYY
        # Pattern 1: DD-MON-YYYY
        match = re.match(r'(\d{1,2})-([a-z]+)-(\d{4})', date_str)
        if match:
            day, month_name, year = match.groups()
            month = DateMatcher.MONTH_NAMES.get(month_name, None)
            if month:
                return (day.zfill(2), month, year)
        
        # Pattern 2: MON-DD-YYYY
        match = re.match(r'([a-z]+)-(\d{1,2})-(\d{4})', date_str)
        if match:
            month_name, day, year = match.groups()
            month = DateMatcher.MONTH_NAMES.get(month_name, None)
            if month:
                return (day.zfill(2), month, year)
        
        # Pattern 3: DD MON YYYY (space separated)
        match = re.match(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', date_str)
        if match:
            day, month_name, year = match.groups()
            month = DateMatcher.MONTH_NAMES.get(month_name, None)
            if month:
                return (day.zfill(2), month, year)
        
        # Pattern 4: MON DD YYYY (space separated)
        match = re.match(r'([a-z]+)\s+(\d{1,2})\s+(\d{4})', date_str)
        if match:
            month_name, day, year = match.groups()
            month = DateMatcher.MONTH_NAMES.get(month_name, None)
            if month:
                return (day.zfill(2), month, year)
        
        # Pattern 5: YYYY MON DD
        match = re.match(r'(\d{4})\s+([a-z]+)\s+(\d{1,2})', date_str)
        if match:
            year, month_name, day = match.groups()
            month = DateMatcher.MONTH_NAMES.get(month_name, None)
            if month:
                return (day.zfill(2), month, year)
        
        return None
    
    @staticmethod
    def date_exists_in_text(date_str: str, text: str) -> bool:
        """
        Check if a date exists in text, handling various representations
        """
        if not date_str or not text:
            return False
        
        day, month, year = DateMatcher.normalize_date(date_str)
        if not (day and month and year):
            # If we can't parse the input date, fall back to simple string matching
            return date_str.lower() in text.lower()
        
        text_lower = text.lower()
        
        # Generate all possible representations of this date
        possible_representations = DateMatcher.generate_date_representations(day, month, year)
        
        # Check if any representation exists in the text
        for rep in possible_representations:
            if rep in text_lower:
                return True
        
        return False
    
    @staticmethod
    def generate_date_representations(day: str, month: str, year: str) -> list:
        """
        Generate all possible text representations of a date
        Input: day='01', month='01', year='2021'
        Output: ['01-01-2021', '01/01/2021', '01 01 2021', 'jan 01 2021', '01 jan 2021', ...]
        Handles both zero-padded (01) and non-padded (1) formats
        """
        representations = []
        
        # Convert to int and back to get both formats
        day_int = int(day)
        month_int = int(month)
        day_str_padded = str(day_int).zfill(2)
        day_str_unpadded = str(day_int)
        month_str_padded = str(month_int).zfill(2)
        month_str_unpadded = str(month_int)
        
        # Generate representations for both padded and unpadded formats
        for d in [day_str_padded, day_str_unpadded]:
            for m in [month_str_padded, month_str_unpadded]:
                # Numeric formats
                representations.append(f"{d}-{m}-{year}")  # DD-MM-YYYY or D-M-YYYY
                representations.append(f"{d}/{m}/{year}")  # DD/MM/YYYY or D/M/YYYY
                representations.append(f"{d} {m} {year}")  # DD MM YYYY or D M YYYY
                representations.append(f"{year}-{m}-{d}")  # YYYY-MM-DD or YYYY-M-D
                representations.append(f"{year}/{m}/{d}")  # YYYY/MM/DD or YYYY/M/D
                representations.append(f"{year} {m} {d}")  # YYYY MM DD or YYYY M D
        
        # With month names (only for day variations, month names are fixed)
        month_names = DateMatcher.get_month_names(month)
        for month_name in month_names:
            for d in [day_str_padded, day_str_unpadded]:
                representations.append(f"{d}-{month_name}-{year}")  # DD-JAN-YYYY or D-JAN-YYYY
                representations.append(f"{d}/{month_name}/{year}")  # DD/JAN/YYYY or D/JAN/YYYY
                representations.append(f"{d} {month_name} {year}")  # DD JAN YYYY or D JAN YYYY
                representations.append(f"{month_name}-{d}-{year}")  # JAN-DD-YYYY or JAN-D-YYYY
                representations.append(f"{month_name}/{d}/{year}")  # JAN/DD/YYYY or JAN/D/YYYY
                representations.append(f"{month_name} {d} {year}")  # JAN DD YYYY or JAN D YYYY
                representations.append(f"{month_name} {d}, {year}")  # JAN DD, YYYY or JAN D, YYYY
                representations.append(f"{year}-{month_name}-{d}")  # YYYY-JAN-DD or YYYY-JAN-D
                representations.append(f"{year} {month_name} {d}")  # YYYY JAN DD or YYYY JAN D
        
        # Remove duplicates while preserving order
        seen = set()
        unique_reps = []
        for rep in representations:
            if rep not in seen:
                seen.add(rep)
                unique_reps.append(rep)
        
        return unique_reps
    
    @staticmethod
    def get_month_names(month_num: str) -> list:
        """
        Get all variations of month name for a month number
        Input: '01' -> Output: ['january', 'jan']
        """
        for full_name, num in DateMatcher.MONTH_NAMES.items():
            if num == month_num:
                # Return full name and 3-letter abbreviation
                if len(full_name) > 3:
                    short_name = full_name[:3]
                    return [full_name, short_name]
                else:
                    return [full_name]
        return []
