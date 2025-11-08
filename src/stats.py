import pandas as pd
import numpy as np
from scipy import stats

def analyze_volatility_hypotheses(df: pd.DataFrame, atr_window: int = 14, ma_window: int = 30) -> pd.DataFrame:
    """
    分析波動率假說，比較高波動日與低波動日之後的平均報酬是否有顯著差異。

    此函式嚴格遵循研究設計，執行以下操作：
    1. 根據 ATR 指標及其移動平均來定義「高波動日」與「低波動日」。
    2. 準備 t+1 的隔日簡單報酬率 (`RET_SIMPLE`) 作為分析目標。
    3. 建立高/低波動日之後的報酬樣本群組。
    4. 使用 Welch's t-test (不假設等變異數) 檢定兩組平均報酬的差異是否顯著。
    5. 回傳一個包含樣本數、平均報酬、t-statistic 和 p-value 的匯總 DataFrame。

    Args:
        df: 包含 'ATR_14', 'RET_SIMPLE' 等特徵的 Pandas DataFrame。
        atr_window: ATR 的計算天期 (預設為 14)。
        ma_window: 用於定義波動狀態的移動平均天期 (預設為 30)。

    Returns:
        一個匯總統計結果的 Pandas DataFrame，包含 'Regime', 'Count',
        'Mean_Return', 'T_Statistic', 'P_Value' 等欄位。
    """
    df_analysis = df.copy()

    # 1. 計算 ATR 的移動平均
    atr_col = f'ATR_{atr_window}'
    df_analysis['ATR_MA'] = df_analysis[atr_col].rolling(window=ma_window).mean()

    # 2. 定義高低波動狀態 (Regime)
    df_analysis['Regime'] = np.where(df_analysis[atr_col] > df_analysis['ATR_MA'], 'High', 'Low')

    # 3. 準備隔日報酬 (目標變數)
    df_analysis['Next_Day_Return'] = df_analysis['RET_SIMPLE'].shift(-1)

    # 4. 建立高低波動樣本群組
    high_vol_returns = df_analysis[df_analysis['Regime'] == 'High']['Next_Day_Return'].dropna()
    low_vol_returns = df_analysis[df_analysis['Regime'] == 'Low']['Next_Day_Return'].dropna()

    # 5. 執行獨立樣本 t-test
    # 使用 equal_var=False 執行 Welch's t-test，這在兩樣本變異數未知時更穩健
    ttest_result = stats.ttest_ind(high_vol_returns, low_vol_returns, equal_var=False, nan_policy='omit')

    # 6. 建立並回傳結果 DataFrame
    results = {
        'Regime': ['High', 'Low'],
        'Count': [len(high_vol_returns), len(low_vol_returns)],
        'Mean_Return': [high_vol_returns.mean(), low_vol_returns.mean()],
        'T_Statistic': [ttest_result.statistic, ttest_result.statistic],
        'P_Value': [ttest_result.pvalue, ttest_result.pvalue]
    }

    results_df = pd.DataFrame(results)

    return results_df
