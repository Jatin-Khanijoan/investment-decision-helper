"""
Data Accessor for NIFTY 50 historical price data.
Provides fast lookup by (Date, Symbol) and historical window queries.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class NiftyDataAccessor:
    """
    Accessor class for NIFTY 50 historical data.
    Handles CSV loading, indexing, and data retrieval.
    """
    
    def __init__(self, csv_path: str = "NIFTY 50-23-01-2025-to-23-01-2026.csv"):
        """
        Initialize the data accessor.
        
        Args:
            csv_path: Path to the NIFTY 50 CSV file
        """
        self.csv_path = csv_path
        self.df = None
        self.train_end_date = None
        self.test_start_date = None
        self.load_data()
        
    def load_data(self):
        """Load CSV data into pandas DataFrame with proper indexing."""
        logger.info(f"Loading data from {self.csv_path}")
        
        # Load CSV - note the spaces in column names
        self.df = pd.read_csv(self.csv_path)
        
        # Clean column names (remove trailing spaces)
        self.df.columns = self.df.columns.str.strip()
        
        # Parse date column
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%d-%b-%Y')
        
        # Sort by date (oldest first)
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
        # Set multi-index for fast lookup (Date as primary index for now)
        # Note: This CSV appears to be NIFTY 50 index data, not individual stocks
        self.df.set_index('Date', inplace=True)
        
        # Calculate train/test split
        self._calculate_train_test_split()
        
        # Verify data completeness
        self._verify_data_completeness()
        
        logger.info(f"Loaded {len(self.df)} rows of data")
        logger.info(f"Date range: {self.df.index.min()} to {self.df.index.max()}")
        
    def _calculate_train_test_split(self):
        """
        Calculate train/test split.
        Training: Jan 2025 - Jun 2025
        Testing: Jul 2025 - Jan 2026
        """
        # Find the mid-point around June 2025
        mid_date = datetime(2025, 7, 1)
        
        # Find closest actual trading date
        dates_before_july = self.df[self.df.index < mid_date].index
        dates_after_july = self.df[self.df.index >= mid_date].index
        
        if len(dates_before_july) > 0:
            self.train_end_date = dates_before_july[-1]
        
        if len(dates_after_july) > 0:
            self.test_start_date = dates_after_july[0]
            
        logger.info(f"Train period: {self.df.index.min()} to {self.train_end_date}")
        logger.info(f"Test period: {self.test_start_date} to {self.df.index.max()}")
        
    def _verify_data_completeness(self):
        """Verify data completeness and identify missing dates."""
        # Check for missing values
        missing_counts = self.df.isnull().sum()
        if missing_counts.any():
            logger.warning(f"Missing values found:\n{missing_counts[missing_counts > 0]}")
        else:
            logger.info("No missing values found in data")
            
        # Check for duplicate dates
        duplicate_dates = self.df.index.duplicated()
        if duplicate_dates.any():
            logger.warning(f"Found {duplicate_dates.sum()} duplicate dates")
        else:
            logger.info("No duplicate dates found")
            
    def get_price(self, date: datetime, price_type: str = 'Close') -> Optional[float]:
        """
        Get price for a specific date.
        
        Args:
            date: Date to lookup
            price_type: Type of price ('Open', 'High', 'Low', 'Close')
            
        Returns:
            Price value or None if not found
        """
        try:
            # Convert to datetime if string
            if isinstance(date, str):
                date = pd.to_datetime(date)
                
            # Normalize to date only (remove time component)
            date = pd.Timestamp(date.date())
            
            if date in self.df.index:
                return float(self.df.loc[date, price_type])
            else:
                logger.warning(f"Date {date} not found in data")
                return None
        except Exception as e:
            logger.error(f"Error getting price for {date}: {e}")
            return None
            
    def get_historical_window(
        self, 
        end_date: datetime, 
        days: int = 30,
        include_end_date: bool = True
    ) -> pd.DataFrame:
        """
        Get historical data window ending at specified date.
        
        Args:
            end_date: End date of the window
            days: Number of trading days to include
            include_end_date: Whether to include the end_date in results
            
        Returns:
            DataFrame with historical data
        """
        try:
            # Convert to datetime if string
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
                
            # Normalize to date only
            end_date = pd.Timestamp(end_date.date())
            
            # Get all dates up to and including end_date
            if include_end_date:
                historical_data = self.df[self.df.index <= end_date]
            else:
                historical_data = self.df[self.df.index < end_date]
                
            # Take last N days
            if len(historical_data) > days:
                historical_data = historical_data.tail(days)
                
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical window: {e}")
            return pd.DataFrame()
            
    def get_price_after_days(
        self, 
        start_date: datetime, 
        days_ahead: int = 7
    ) -> Optional[float]:
        """
        Get closing price N days after a given date.
        Useful for calculating outcomes in backtesting.
        
        Args:
            start_date: Starting date
            days_ahead: Number of trading days ahead
            
        Returns:
            Closing price or None if not found
        """
        try:
            # Convert to datetime if string
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
                
            # Normalize to date only
            start_date = pd.Timestamp(start_date.date())
            
            # Get all dates after start_date
            future_dates = self.df[self.df.index > start_date]
            
            # Take the Nth trading day
            if len(future_dates) >= days_ahead:
                target_date = future_dates.index[days_ahead - 1]
                return float(self.df.loc[target_date, 'Close'])
            else:
                logger.warning(f"Not enough data to look {days_ahead} days ahead from {start_date}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting price {days_ahead} days ahead: {e}")
            return None
            
    def get_train_data(self) -> pd.DataFrame:
        """Get training data (Jan-Jun 2025)."""
        return self.df[self.df.index <= self.train_end_date]
        
    def get_test_data(self) -> pd.DataFrame:
        """Get testing data (Jul-Jan 2026)."""
        return self.df[self.df.index >= self.test_start_date]
        
    def get_return_percentage(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[float]:
        """
        Calculate return percentage between two dates.
        
        Args:
            start_date: Starting date
            end_date: Ending date
            
        Returns:
            Return percentage or None if data not found
        """
        start_price = self.get_price(start_date, 'Close')
        end_price = self.get_price(end_date, 'Close')
        
        if start_price and end_price and start_price > 0:
            return ((end_price - start_price) / start_price) * 100
        return None


if __name__ == "__main__":
    # Test the data accessor
    logging.basicConfig(level=logging.INFO)
    
    accessor = NiftyDataAccessor()
    
    # Test get_price
    test_date = datetime(2025, 6, 1)
    price = accessor.get_price(test_date)
    print(f"Price on {test_date}: {price}")
    
    # Test historical window
    window = accessor.get_historical_window(test_date, days=7)
    print(f"\nLast 7 days before {test_date}:")
    print(window[['Open', 'Close', 'High', 'Low']])
    
    # Test price after days
    future_price = accessor.get_price_after_days(test_date, days_ahead=7)
    print(f"\nPrice 7 days after {test_date}: {future_price}")
    
    # Test return calculation
    end_date = datetime(2025, 6, 10)
    return_pct = accessor.get_return_percentage(test_date, end_date)
    if return_pct:
        print(f"\nReturn from {test_date} to {end_date}: {return_pct:.2f}%")
    else:
        print(f"\nCould not calculate return (dates not found in data)")
