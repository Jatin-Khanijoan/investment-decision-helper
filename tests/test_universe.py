from providers.utils import validate_symbol, NIFTY50_SYMBOLS


def test_nifty50_universe():
    """Test only NIFTY50 symbols accepted"""
    universe = NIFTY50_SYMBOLS

    # Valid symbols
    assert validate_symbol("RELIANCE", universe)
    assert validate_symbol("TCS", universe)
    assert validate_symbol("INFY", universe)

    # Invalid symbols
    assert not validate_symbol("AAPL", universe)
    assert not validate_symbol("GOOGL", universe)
    assert not validate_symbol("INVALID", universe)


def test_universe_size():
    """Test universe has expected NIFTY50 count"""
    universe = NIFTY50_SYMBOLS
    # Should have 50 or 51 companies (sometimes includes extras)
    assert 50 <= len(universe) <= 51
