# src/viz.py
# 視覺化與績效報告模組

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # 使用非互動式後端，避免在伺服器上出錯
import matplotlib.pyplot as plt

def plot_equity_curve(equity_curve: pd.DataFrame, output_path: str, performance_metrics: dict = None):
    """
    繪製權益曲線圖並將其保存為檔案。

    Args:
        equity_curve (pd.DataFrame): 包含 'equity' 欄位的 DataFrame，索引為日期。
        output_path (str): 儲存圖表的檔案路徑 (例如 'equity_curve.jpg')。
        performance_metrics (dict, optional): 包含績效指標的字典。如果提供，
                                              指標將會被顯示在圖表的標題中。
    """
    plt.style.use('seaborn-v0_8-darkgrid') # 使用較美觀的樣式
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(equity_curve.index, equity_curve['equity'], label='Equity Curve', color='royalblue')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Equity', fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # 格式化標題
    title = "Strategy Equity Curve"
    if performance_metrics:
        total_return = performance_metrics.get('total_return', 0) * 100
        max_drawdown = performance_metrics.get('max_drawdown', 0) * 100
        sharpe = performance_metrics.get('sharpe_ratio', 0)
        title += (
            f"\\n"
            f"Total Return: {total_return:.2f}% | "
            f"Max Drawdown: {max_drawdown:.2f}% | "
            f"Sharpe Ratio: {sharpe:.2f}"
        )
    ax.set_title(title, fontsize=16, pad=20)

    # 改善圖表外觀
    plt.tight_layout()
    fig.savefig(output_path, format='jpg', dpi=150) # 提高解析度
    plt.close(fig) # 釋放記憶體

def calculate_performance_metrics(equity_curve: pd.DataFrame, trading_days_per_year: int = 252) -> dict:
    """
    計算並返回多個關鍵績效指標。

    Args:
        equity_curve (pd.DataFrame): 包含 'equity' 欄位的 DataFrame。
        trading_days_per_year (int): 每年的交易日數，用於年化計算。

    Returns:
        dict: 包含績效指標的字典。
    """

    # 1. Total Return
    total_return = (equity_curve['equity'].iloc[-1] - equity_curve['equity'].iloc[0]) / equity_curve['equity'].iloc[0]

    # 2. Max Drawdown
    cumulative_max = equity_curve['equity'].cummax()
    drawdown = (equity_curve['equity'] - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()

    # 3. Sharpe Ratio
    daily_returns = equity_curve['equity'].pct_change().dropna()

    # 如果沒有足夠的數據點，無法計算夏普比率
    if len(daily_returns) < 2:
        sharpe_ratio = 0.0
    else:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(trading_days_per_year)

    return {
        'total_return': total_return,
        'max_drawdown': abs(max_drawdown), # 通常回報為正數
        'sharpe_ratio': sharpe_ratio if not np.isnan(sharpe_ratio) else 0.0
    }
