import pandas as pd
import numpy as np
import pytest
from src.signal import generate_signals, adjust_signals_for_execution

# 定義測試檔案路徑
FEATURES_DATA_PATH = "tests/sample_parquets/features_for_stats.parquet"

@pytest.fixture(scope="module")
def sample_features_dataframe() -> pd.DataFrame:
    """載入訊號生成用的特徵 DataFrame。"""
    return pd.read_parquet(FEATURES_DATA_PATH)

def test_generate_basic_signals(sample_features_dataframe):
    """測試基礎觸發規則及輔助欄位。"""
    high_vol_trend = -1
    df_with_signals = generate_signals(sample_features_dataframe, high_vol_trend=high_vol_trend, use_sma_filter=False)

    df_verify = sample_features_dataframe.copy()
    df_verify['ATR_30_MA'] = df_verify['ATR_14'].rolling(window=30).mean()
    df_verify['is_high_vol'] = df_verify['ATR_14'] > df_verify['ATR_30_MA']
    first_high_vol_day = df_verify[df_verify['is_high_vol']].index[0]

    assert df_with_signals.loc[first_high_vol_day, 'signal'] == -1
    assert df_with_signals.loc[first_high_vol_day, 'signal_reason'] == "High Volatility Short"
    # 驗證新增的輔助欄位
    assert df_with_signals.loc[first_high_vol_day, 'signal_generated_at'] == first_high_vol_day
    assert df_with_signals.loc[first_high_vol_day, 'signal_exec_when'] == first_high_vol_day + pd.Timedelta(days=1)

def test_generate_signals_with_sma_filter(sample_features_dataframe):
    """測試 SMA 過濾器。"""
    high_vol_trend = -1
    df_with_signals = generate_signals(sample_features_dataframe, high_vol_trend=high_vol_trend, use_sma_filter=True)

    df_verify = sample_features_dataframe.copy()
    df_verify['ATR_30_MA'] = df_verify['ATR_14'].rolling(window=30).mean()
    df_verify['is_high_vol'] = df_verify['ATR_14'] > df_verify['ATR_30_MA']
    df_verify['is_sma_down'] = df_verify['SMA_20'].diff() < 0

    first_valid_short_day = df_verify[df_verify['is_high_vol'] & df_verify['is_sma_down']].index[0]
    assert df_with_signals.loc[first_valid_short_day, 'signal'] == -1

    first_filtered_day = df_verify[df_verify['is_high_vol'] & ~df_verify['is_sma_down']].index[0]
    assert df_with_signals.loc[first_filtered_day, 'signal'] == 0
    assert df_with_signals.loc[first_filtered_day, 'signal_reason'] == "Filtered by SMA"

def test_signal_representation(sample_features_dataframe):
    """驗證訊號表示格式。"""
    df_with_signals = generate_signals(sample_features_dataframe, high_vol_trend=1, use_sma_filter=False)

    assert 'signal' in df_with_signals.columns
    assert 'signal_reason' in df_with_signals.columns
    assert 'signal_generated_at' in df_with_signals.columns
    assert 'signal_exec_when' in df_with_signals.columns
    assert pd.api.types.is_integer_dtype(df_with_signals['signal'])
    assert df_with_signals['signal'].isin([-1, 0, 1]).all()

def test_handle_execution_delays():
    """
    測試處理非交易日延遲與訊號取消的邏輯。
    """
    # 1. 建立一個包含非交易日的 DataFrame
    dates = pd.to_datetime(['2023-01-02', '2023-01-03', '2023-01-06', '2023-01-10'])
    data = {'signal': [0, 1, 0, 0]}
    df = pd.DataFrame(data, index=dates)
    df['signal_generated_at'] = pd.NaT
    df['signal_exec_when'] = pd.NaT
    df['signal_reason'] = ''

    # 2. 手動設定一個訊號
    # 訊號在 01-03 (週二) 產生，理想執行日在 01-04 (週三)，但這天是非交易日
    signal_day = pd.to_datetime('2023-01-03')
    df.loc[signal_day, 'signal'] = 1
    df.loc[signal_day, 'signal_reason'] = "Test Signal"
    df.loc[signal_day, 'signal_generated_at'] = signal_day
    df.loc[signal_day, 'signal_exec_when'] = signal_day + pd.Timedelta(days=1)

    # 3. 執行延遲調整函式
    df_adjusted = adjust_signals_for_execution(df, max_delay_days=3)

    # 4. 驗證延遲執行
    # 理想執行日 01-04，下一個交易日是 01-06，延遲 2 天 <= 3 天
    assert df_adjusted.loc[signal_day, 'signal'] == 1
    assert df_adjusted.loc[signal_day, 'signal_exec_when'] == pd.to_datetime('2023-01-06')
    assert "Delayed 2d" in df_adjusted.loc[signal_day, 'signal_reason']

    # 5. 驗證訊號取消
    # 將最大延遲設為 1 天
    df_cancelled = adjust_signals_for_execution(df, max_delay_days=1)
    # 延遲 2 天 > 1 天，訊號應被取消
    assert df_cancelled.loc[signal_day, 'signal'] == 0
    assert "Cancelled" in df_cancelled.loc[signal_day, 'signal_reason']
