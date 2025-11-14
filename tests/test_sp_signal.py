import pandas as pd
import numpy as np
import pytest
from src.sp_signal import generate_signals, adjust_signals_for_execution

# 定義測試檔案路徑
FEATURES_DATA_PATH = "tests/sample_parquets/features_for_stats.parquet"

@pytest.fixture(scope="module")
def sample_features_dataframe() -> pd.DataFrame:
    """載入訊號生成用的特徵 DataFrame。"""
    df = pd.read_parquet(FEATURES_DATA_PATH)
    if 'ATR_14' not in df.columns:
        df['ATR_14'] = df['Close'].rolling(14).mean()
    return df

def test_generate_basic_signals(sample_features_dataframe):
    """測試基礎觸發規則及輔助欄位。"""
    high_vol_trend = -1
    df_with_signals = generate_signals(
        sample_features_dataframe,
        high_vol_trend=high_vol_trend,
        atr_period=14,
        atr_multiplier=1.0
    )

    df_verify = sample_features_dataframe.copy()
    df_verify['ATR_MA'] = df_verify['ATR_14'].rolling(window=30).mean()
    df_verify['is_high_vol'] = df_verify['ATR_14'] > df_verify['ATR_MA']

    first_high_vol_day_index = df_verify['is_high_vol'].idxmax()

    assert df_with_signals.loc[first_high_vol_day_index, 'signal'] == high_vol_trend
    # 驗證輔助欄位的存在與內容
    assert df_with_signals.loc[first_high_vol_day_index, 'signal_reason'] == "High Volatility Short"
    assert df_with_signals.loc[first_high_vol_day_index, 'signal_generated_at'] == first_high_vol_day_index
    assert df_with_signals.loc[first_high_vol_day_index, 'signal_exec_when'] == first_high_vol_day_index + pd.Timedelta(days=1)


def test_signal_representation(sample_features_dataframe):
    """驗證訊號表示格式。"""
    df_with_signals = generate_signals(sample_features_dataframe, high_vol_trend=1)

    assert 'signal' in df_with_signals.columns
    # 驗證輔助欄位的存在
    assert 'signal_reason' in df_with_signals.columns
    assert 'signal_generated_at' in df_with_signals.columns
    assert 'signal_exec_when' in df_with_signals.columns

    assert pd.api.types.is_integer_dtype(df_with_signals['signal'])
    assert df_with_signals['signal'].isin([-1, 0, 1]).all()

def test_handle_execution_delays():
    """
    測試處理非交易日延遲與訊號取消的邏輯。
    """
    dates = pd.to_datetime(['2023-01-02', '2023-01-03', '2023-01-06', '2023-01-10'])
    data = {'signal': [0, 1, 0, 0]}
    df = pd.DataFrame(data, index=dates)
    df['signal_generated_at'] = pd.NaT
    df['signal_exec_when'] = pd.NaT
    df['signal_reason'] = ''

    signal_day = pd.to_datetime('2023-01-03')
    df.loc[signal_day, 'signal'] = 1
    df.loc[signal_day, 'signal_reason'] = "Test Signal"
    df.loc[signal_day, 'signal_generated_at'] = signal_day
    df.loc[signal_day, 'signal_exec_when'] = signal_day + pd.Timedelta(days=1)

    df_adjusted = adjust_signals_for_execution(df, max_delay_days=3)

    assert df_adjusted.loc[signal_day, 'signal'] == 1
    assert df_adjusted.loc[signal_day, 'signal_exec_when'] == pd.to_datetime('2023-01-06')
    assert "Delayed 2d" in df_adjusted.loc[signal_day, 'signal_reason']

    df_cancelled = adjust_signals_for_execution(df, max_delay_days=1)
    assert df_cancelled.loc[signal_day, 'signal'] == 0
    assert "Cancelled" in df_cancelled.loc[signal_day, 'signal_reason']

def test_buy_and_hold_signals(sample_features_dataframe):
    from src.sp_signal import generate_buy_and_hold_signals
    df_signal = generate_buy_and_hold_signals(sample_features_dataframe)
    assert df_signal.iloc[0]['signal'] == 1
    assert df_signal.iloc[-2]['signal'] == 0
    assert df_signal.iloc[-1]['signal'] == 0
    # 驗證輔助欄位的存在
    assert 'signal_reason' in df_signal.columns
    assert 'signal_exec_when' in df_signal.columns
