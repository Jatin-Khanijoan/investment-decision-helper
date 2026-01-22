"""
Technical indicator calculations for backtesting and analysis.
Pre-computes common indicators from price data.
"""
import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calculate technical indicators from OHLCV data.
    """
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            Series with RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Series of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            
        Returns:
            Dictionary with MACD, signal, and histogram
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
        
    @staticmethod
    def calculate_moving_averages(
        prices: pd.Series,
        periods: list = [10, 20, 50, 200]
    ) -> Dict[str, pd.Series]:
        """
        Calculate Simple Moving Averages for multiple periods.
        
        Args:
            prices: Series of closing prices
            periods: List of periods to calculate
            
        Returns:
            Dictionary of SMA series
        """
        mas = {}
        for period in periods:
            mas[f'sma_{period}'] = prices.rolling(window=period).mean()
        return mas
        
    @staticmethod
    def calculate_volatility(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate rolling volatility (standard deviation of returns).
        
        Args:
            prices: Series of closing prices
            period: Period for volatility calculation
            
        Returns:
            Series with volatility values (annualized)
        """
        returns = prices.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
        return volatility
        
    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        num_std: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of closing prices
            period: Period for moving average
            num_std: Number of standard deviations
            
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        return {
            'bb_upper': sma + (std * num_std),
            'bb_middle': sma,
            'bb_lower': sma - (std * num_std)
        }
        
    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (ATR).
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            period: ATR period
            
        Returns:
            Series with ATR values
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
        
    @staticmethod
    def identify_regime_changes(
        prices: pd.Series,
        volatility: pd.Series,
        vol_threshold: float = 0.3
    ) -> pd.Series:
        """
        Identify major market regime changes based on volatility spikes.
        
        Args:
            prices: Series of closing prices
            volatility: Series of volatility values
            vol_threshold: Threshold for high volatility
            
        Returns:
            Series marking regime changes (1 = high vol, 0 = normal)
        """
        high_vol_regime = (volatility > vol_threshold).astype(int)
        return high_vol_regime
        
    @classmethod
    def calculate_all_indicators(
        cls,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate all technical indicators for a DataFrame.
        
        Args:
            df: DataFrame with OHLCV data (Open, High, Low, Close, Volume)
            
        Returns:
            DataFrame with all indicators added
        """
        logger.info("Calculating technical indicators")
        
        result = df.copy()
        
        # RSI
        result['rsi'] = cls.calculate_rsi(df['Close'])
        
        # MACD
        macd = cls.calculate_macd(df['Close'])
        result['macd'] = macd['macd']
        result['macd_signal'] = macd['signal']
        result['macd_histogram'] = macd['histogram']
        
        # Moving Averages
        mas = cls.calculate_moving_averages(df['Close'])
        for name, series in mas.items():
            result[name] = series
            
        # Volatility
        result['volatility'] = cls.calculate_volatility(df['Close'])
        
        # Bollinger Bands
        bb = cls.calculate_bollinger_bands(df['Close'])
        for name, series in bb.items():
            result[name] = series
            
        # ATR
        result['atr'] = cls.calculate_atr(df['High'], df['Low'], df['Close'])
        
        # Regime changes
        result['high_vol_regime'] = cls.identify_regime_changes(
            df['Close'],
            result['volatility']
        )
        
        logger.info(f"Calculated {len(result.columns) - len(df.columns)} indicators")
        return result


def precompute_indicators_to_csv(
    input_csv: str,
    output_csv: str = "nifty50_with_indicators.csv"
):
    """
    Precompute indicators and save to CSV for faster backtesting.
    
    Args:
        input_csv: Path to input CSV
        output_csv: Path to output CSV with indicators
    """
    logger.info(f"Loading data from {input_csv}")
    
    df = pd.read_csv(input_csv)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Calculate indicators
    df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)
    
    # Save to CSV
    df_with_indicators.to_csv(output_csv, index=False)
    logger.info(f"Saved indicators to {output_csv}")
    
    # Log some statistics
    logger.info("\nData Quality Summary:")
    logger.info(f"Total rows: {len(df_with_indicators)}")
    logger.info(f"Date range: {df_with_indicators['Date'].min()} to {df_with_indicators['Date'].max()}")
    
    # Identify high volatility periods
    high_vol_days = df_with_indicators[df_with_indicators['high_vol_regime'] == 1]
    if len(high_vol_days) > 0:
        logger.info(f"\nHigh volatility periods: {len(high_vol_days)} days")
        logger.info(f"Dates: {high_vol_days['Date'].tolist()[:5]}...")  # Show first 5
        
    return df_with_indicators


if __name__ == "__main__":
    # Test indicator calculations
    logging.basicConfig(level=logging.INFO)
    
    df = precompute_indicators_to_csv(
        "NIFTY 50-23-01-2025-to-23-01-2026.csv",
        "nifty50_with_indicators.csv"
    )
    
    print("\nSample indicators:")
    print(df[['Date', 'Close', 'rsi', 'macd', 'volatility']].tail(10))
