import pandas as pd
import numpy as np
import pytest
from scipy import stats
from src.stats import analyze_volatility_hypotheses # 預期從 src/stats.py 導入函式

# 定義測試檔案路徑
FEATURES_DATA_PATH = "tests/sample_parquets/features_for_stats.parquet"

@pytest.fixture(scope="module")
def sample_features_dataframe() -> pd.DataFrame:
    """載入統計分析用的特徵 DataFrame。"""
    return pd.read_parquet(FEATURES_DATA_PATH)

def get_expected_stats_results(df: pd.DataFrame) -> dict:
    """
    手動計算預期的統計結果，作為測試的基準。
    """
    # 1. 定義高低波動日
    df['ATR_30_MA'] = df['ATR_14'].rolling(window=30).mean()
    df['Regime'] = np.where(df['ATR_14'] > df['ATR_30_MA'], 'High', 'Low')

    # 2. 準備隔日報酬
    df['Next_Day_Return'] = df['RET_SIMPLE'].shift(-1)

    # 3. 建立高低波動樣本群組
    high_vol_returns = df[df['Regime'] == 'High']['Next_Day_Return'].dropna()
    low_vol_returns = df[df['Regime'] == 'Low']['Next_Day_Return'].dropna()

    # 4. 執行 T-test
    ttest_result = stats.ttest_ind(high_vol_returns, low_vol_returns, equal_var=False) # Welch's t-test

    return {
        'high_vol_count': len(high_vol_returns),
        'high_vol_mean_return': high_vol_returns.mean(),
        'low_vol_count': len(low_vol_returns),
        'low_vol_mean_return': low_vol_returns.mean(),
        'p_value': ttest_result.pvalue,
        't_statistic': ttest_result.statistic
    }

def test_volatility_analysis_results(sample_features_dataframe):
    """
    測試 analyze_volatility_hypotheses 函式的統計結果是否與預期一致。
    """
    # 獲取預期結果
    expected_results = get_expected_stats_results(sample_features_dataframe.copy())

    # 執行目標函式 (目前應不存在)
    actual_results_df = analyze_volatility_hypotheses(sample_features_dataframe)

    # 從 DataFrame 中提取實際結果
    high_vol_row = actual_results_df[actual_results_df['Regime'] == 'High'].iloc[0]
    low_vol_row = actual_results_df[actual_results_df['Regime'] == 'Low'].iloc[0]

    # 斷言：樣本數
    assert high_vol_row['Count'] == expected_results['high_vol_count']
    assert low_vol_row['Count'] == expected_results['low_vol_count']

    # 斷言：平均報酬
    assert np.isclose(high_vol_row['Mean_Return'], expected_results['high_vol_mean_return'])
    assert np.isclose(low_vol_row['Mean_Return'], expected_results['low_vol_mean_return'])

    # 斷言：P-value (只需比較一次)
    # 我們假設函式回傳的 p-value 會放在 DataFrame 的某個地方，這裡假設是 'P_Value' 欄
    assert np.isclose(actual_results_df['P_Value'].iloc[0], expected_results['p_value'])
