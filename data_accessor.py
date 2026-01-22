"""
Data accessor for NIFTY 50 historical price data.
Loads and manages multiple years of CSV data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
import logging
import os

logger = logging.getLogger(__name__)


class NiftyDataAccessor:
    """
    Accessor for NIFTY 50 historical price data from multiple CSV files.
    """
    
    def __init__(self, csv_files: List[str] = None):
        """
        Initialize NiftyDataAccessor with historical data from multiple CSV files.
        
        Args:
            csv_files: List of CSV file paths to load. If None, loads all available NIFTY files.
        """
        self.logger = logging.getLogger(__name__)
        
        # Default to all available NIFTY 50 files (2021-2026)
        if csv_files is None:
            csv_files = [
                "NIFTY 50-22-01-2021-to-22-01-2022.csv",
                "NIFTY 50-22-01-2022-to-22-01-2023.csv",
                "NIFTY 50-22-01-2023-to-22-01-2024.csv",
                "NIFTY 50-22-01-2024-to-22-01-2025.csv",
                "NIFTY 50-23-01-2025-to-23-01-2026.csv"
            ]
        
        # Load and concatenate all CSV files
        all_data = []
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                self.logger.warning(f"File not found: {csv_file}, skipping")
                continue
                
            self.logger.info(f"Loading data from {csv_file}")
            df_chunk = pd.read_csv(csv_file)
            
            # Handle date column (may have spaces)
            date_col = [col for col in df_chunk.columns if 'date' in col.lower()][0]
            df_chunk['Date'] = pd.to_datetime(df_chunk[date_col], format='%d-%b-%Y')
            
            # Keep only necessary columns
            columns_to_keep = ['Date']
            for col in ['Open', 'High', 'Low', 'Close', 'Shares Traded', 'Turnover']:
                matching = [c for c in df_chunk.columns if col.lower() in c.lower()]
                if matching:
                    df_chunk = df_chunk.rename(columns={matching[0]: col})
                    columns_to_keep.append(col)
            
            all_data.append(df_chunk[columns_to_keep])
        
        if not all_data:
            raise ValueError("No CSV files could be loaded")
        
        # Concatenate all dataframes
        self.df = pd.concat(all_data, ignore_index=True)
        
        # Sort by date and remove duplicates
        self.df = self.df.sort_values('Date')
        self.df = self.df.drop_duplicates(subset=['Date'], keep='first')
        
        # Set Date as index
        self.df.set_index('Date', inplace=True)
        
        # Log data info
        self.logger.info(f"Loaded {len(self.df)} total trading days")
        self.logger.info(f"Date range: {self.df.index.min()} to {self.df.index.max()}")
        
        # Define train/test split (use 2021-2024 for training, 2024-2026 for testing)
        self.train_start = datetime(2021, 1, 22)
        self.train_end = datetime(2024, 1, 22)
        self.test_start = datetime(2024, 1, 23)
        self.test_end = datetime(2026, 1, 22)
        
        # Count days in each split
        train_mask = (self.df.index >= self.train_start) & (self.df.index <= self.train_end)
        test_mask = (self.df.index >= self.test_start) & (self.df.index <= self.test_end)
        
        self.logger.info(f"Train period: {self.train_start.date()} to {self.train_end.date()}")
        self.logger.info(f"Train days: {train_mask.sum()}")
        self.logger.info(f"Test period: {self.test_start.date()} to {self.test_end.date()}")
        self.logger.info(f"Test days: {test_mask.sum()}")
        
        # Data quality checks
        if self.df.isnull().any().any():
            null_counts = self.df.isnull().sum()
            self.logger.warning(f"Missing values found: {null_counts[null_counts > 0]}")
        else:
            self.logger.info("No missing values found in data")
        
        # Check for duplicates
        if self.df.index.duplicated().any():
            self.logger.warning(f"Found {self.df.index.duplicated().sum()} duplicate dates")
        else:
            self.logger.info("No duplicate dates found")
        
    def get_price(self, date: datetime, price_type: str = 'Close') -> Optional[float]:
        """
        Get price for a specific date.
        
        Args:
            date: Target date
            price_type: 'Open', 'High', 'Low', or 'Close'
            
        Returns:
            Price value or None if not found
        """
        try:
            return self.df.loc[date, price_type]
        except KeyError:
            # Try finding closest date
            closest_date = self.df.index[self.df.index >= date][0] if any(self.df.index >= date) else None
            if closest_date and (closest_date - date).days <= 3:  # Within 3 days
                return self.df.loc[closest_date, price_type]
            return None
            
    def get_price_after_days(self, start_date: datetime, days_ahead: int = 7) -> Optional[float]:
        """
        Get price N trading days after start_date.
        
        Args:
            start_date: Starting date
            days_ahead: Number of trading days to look ahead
            
        Returns:
            Price or None if not available
        """
        try:
            # Get all dates after start_date
            future_dates = self.df.index[self.df.index > start_date]
            
            if len(future_dates) < days_ahead:
                return None
                
            # Get the Nth trading day
            target_date = future_dates[days_ahead - 1]
            return self.df.loc[target_date, 'Close']
        except (IndexError, KeyError):
            return None
            
    def get_historical_window(
        self, 
        end_date: datetime, 
        days: int = 20,
        include_end_date: bool = False
    ) -> pd.DataFrame:
        """
        Get historical data window before (and optionally including) end_date.
        
        Args:
            end_date: End date of window
            days: Number of days to include
            include_end_date: Whether to include end_date in window
            
        Returns:
            DataFrame with historical data
        """
        if include_end_date:
            mask = self.df.index <= end_date
        else:
            mask = self.df.index < end_date
            
        historical = self.df[mask].tail(days)
        return historical
        
    def calculate_return_percentage(self, start_date: datetime, end_date: datetime) -> Optional[float]:
        """
        Calculate return percentage between two dates.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Return percentage or None
        """
        start_price = self.get_price(start_date, 'Close')
        end_price = self.get_price(end_date, 'Close')
        
        if start_price and end_price and start_price > 0:
            return ((end_price - start_price) / start_price) * 100
        return None


if __name__ == "__main__":
    # Test the accessor with all 5 years of data
    logging.basicConfig(level=logging.INFO)
    
    accessor = NiftyDataAccessor()
    
    print("\nData Summary:")
    print(f"Total days: {len(accessor.df)}")
    print(f"Date range: {accessor.df.index.min().date()} to {accessor.df.index.max().date()}")
    print(f"\nFirst few records:")
    print(accessor.df.head())
    print(f"\nLast few records:")
    print(accessor.df.tail())
    
    # Test price lookup
    test_date = datetime(2022, 6, 15)
    price = accessor.get_price(test_date)
    print(f"\nPrice on {test_date.date()}: {price}")
    
    # Test forward lookup
    price_after = accessor.get_price_after_days(test_date, days_ahead=7)
    print(f"Price 7 days later: {price_after}")
    
    if price and price_after:
        ret = ((price_after - price) / price) * 100
        print(f"7-day return: {ret:.2f}%")
