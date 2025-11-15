import pandas as pd
import numpy as np
import pytest
from src.sp_signal import generate_bollinger_band_signals

def test_bollinger_band_signal_logic():
    """
    驗證布林帶策略一個完整的、簡潔的交易週期。
    """
    # --- 1. 建立測試 DataFrame ---
    # 這個 DataFrame 精確地模擬了一個做多和一個做空的完整週期
    data = {
        # 'Close' prices are crafted to hit specific triggers
        'Close': [
            100,  # Day 0: Initial state
            105,  # Day 1: In uptrend, no signal
            95,   # Day 2: In uptrend, price dips below lower BB -> LONG ENTRY
            100,  # Day 3: Hold long position
            110,  # Day 4: Price hits upper BB -> LONG EXIT
            100,  # Day 5: In downtrend, no signal
            103,  # Day 6: In downtrend, price hits upper BB -> SHORT ENTRY
            85,   # Day 7: Price hits lower BB -> SHORT EXIT
        ],
        # 'SMA_200' defines the major trend
        'SMA_200': [
            90, 90, 90, 90, 90,  # Uptrend period
            105, 105, 105       # Downtrend period
        ],
        # Bollinger Bands define the entry/exit triggers
        'BB_upper_20_2_0': [
            104, 106, 103, 102, 108,  # Upper band for uptrend
            104, 102, 98              # Upper band for downtrend
        ],
        'BB_lower_20_2_0': [
            96, 98, 97, 96, 99,   # Lower band for uptrend
            98, 96, 88            # Lower band for downtrend
        ]
    }
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=len(data['Close'])))
    df = pd.DataFrame(data, index=dates)

    # --- 2. 執行訊號生成 ---
    signals = generate_bollinger_band_signals(
        df=df,
        sma_long_period=200,
        bband_period=20,
        bband_stddev=2.0
    )['signal'].to_list()

    # --- 3. 定義預期結果 ---
    # The signal represents the desired POSITION at the END of each day.
    expected_signals = [
        0,  # Day 0: Flat
        0,  # Day 1: Flat (Close > SMA, but Close > BB_lower)
        1,  # Day 2: LONG (Close > SMA, and Close < BB_lower)
        1,  # Day 3: HOLD LONG
        0,  # Day 4: FLAT (Long profit take, Close > BB_upper)
        0,  # Day 5: FLAT (Close < SMA, but Close < BB_upper)
        -1, # Day 6: SHORT (Close < SMA, and Close > BB_upper)
        0,  # Day 7: FLAT (Short profit take, Close < BB_lower)
    ]

    # --- 4. 斷言 ---
    assert signals == expected_signals, f"訊號序列不匹配！\\n得到: {signals}\\n預期: {expected_signals}"

