import pandas as pd
import numpy as np
from scipy import stats

def run_statistical_tests(df: pd.DataFrame, significance_level: float = 0.05, atr_period: int = 14) -> dict:
    """
    執行波動率假說的 t-test 檢定。

    Args:
        df (pd.DataFrame): 包含特徵的 DataFrame (需要 'ATR_X' 和 'RET_SIMPLE')。
        significance_level (float): 統計顯著性水準。
        atr_period (int): 用於尋找 ATR 欄位的週期。

    Returns:
        dict: 包含統計檢定結果的摘要字典。
    """
    df_analysis = df.copy()
    atr_col = f'ATR_{atr_period}'

    if atr_col not in df_analysis.columns:
        raise ValueError(f"錯誤: 找不到 '{atr_col}' 欄位。請先執行特徵工程。")
    if 'RET_SIMPLE' not in df_analysis.columns:
        raise ValueError("錯誤: 找不到 'RET_SIMPLE' 欄位。")

    # 定義高低波動狀態
    atr_ma = df_analysis[atr_col].rolling(window=30).mean()
    df_analysis['Regime'] = np.where(df_analysis[atr_col] > atr_ma, 'High', 'Low')
    df_analysis['Next_Day_Return'] = df_analysis['RET_SIMPLE'].shift(-1)

    high_vol_returns = df_analysis[df_analysis['Regime'] == 'High']['Next_Day_Return'].dropna()
    low_vol_returns = df_analysis[df_analysis['Regime'] == 'Low']['Next_Day_Return'].dropna()

    if len(high_vol_returns) < 2 or len(low_vol_returns) < 2:
        return {
            "error": "樣本數不足，無法執行 t-test。",
            "high_vol_count": len(high_vol_returns),
            "low_vol_count": len(low_vol_returns)
        }

    # 執行 Welch's t-test
    ttest_result = stats.ttest_ind(high_vol_returns, low_vol_returns, equal_var=False)

    # 建立結果摘要
    summary = {
        "hypothesis": "檢定高波動日與低波動日之後的平均報酬是否存在顯著差異",
        "t_statistic": ttest_result.statistic,
        "p_value": ttest_result.pvalue,
        "significance_level": significance_level,
        "is_significant": ttest_result.pvalue < significance_level,
        "high_vol_mean_return": high_vol_returns.mean(),
        "low_vol_mean_return": low_vol_returns.mean(),
        "high_vol_count": len(high_vol_returns),
        "low_vol_count": len(low_vol_returns)
    }
    return summary
