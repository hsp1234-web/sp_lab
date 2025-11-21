"""
步驟 4：策略 4 (真假外資) 回測腳本
說明：
本腳本負責實現「策略4：真假外資避險」的邏輯。
利用外資買賣超與匯率變動的關係，判斷外資買盤的性質（真買進 vs 假避險）。

策略邏輯:
1. 篩選外資買超 (> 0) 的日子。
2. 觀察當日匯率變動 (USDTWD):
   - Group A (真外資): 匯率大幅下降 (台幣升值) -> 資金匯入，強烈看多。
   - Group B (假外資/避險): 匯率大幅上升 (台幣貶值) -> 資金匯出，可能為期貨避險或短線。
   - Group C (中性): 匯率變動不大。
3. 比較各組後續 N 日的報酬率與 Sharpe Ratio。

執行方式：
uv run python scripts/04_strategy_forex.py
"""

import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('strategy_forex.log', mode='w', encoding='utf-8')
    ]
)

# --- 全域設定 ---
PROCESSED_DATA_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_backtest(df: pd.DataFrame, hold_days: int = 10):
    """
    執行真假外資策略回測。
    """
    logging.info("--- 開始執行策略 4 (真假外資) 回測 ---")

    # 檢查必要欄位
    required_cols = ['Foreign_Investor_Buy', 'USDTWD_Close', 'TWII_Close']
    for col in required_cols:
        if col not in df.columns:
            logging.error(f"錯誤：數據集缺少必要欄位 '{col}'。無法執行策略。")
            return

    # 1. 篩選外資買超的日子
    foreign_buy_mask = df['Foreign_Investor_Buy'] > 0
    
    # 2. 計算匯率變動率
    df['USDTWD_Ret'] = df['USDTWD_Close'].pct_change()
    
    # 定義匯率變動門檻 (例如 0.1%)
    threshold = 0.001 

    # 3. 分組
    # Group A: 外資買 + 台幣升值 (匯率跌) -> 真外資
    group_a_mask = foreign_buy_mask & (df['USDTWD_Ret'] < -threshold)
    
    # Group B: 外資買 + 台幣貶值 (匯率漲) -> 假外資/避險
    group_b_mask = foreign_buy_mask & (df['USDTWD_Ret'] > threshold)
    
    logging.info(f"Group A (真外資) 樣本數: {group_a_mask.sum()}")
    logging.info(f"Group B (假外資) 樣本數: {group_b_mask.sum()}")

    if group_a_mask.sum() == 0 or group_b_mask.sum() == 0:
        logging.warning("樣本數不足，無法進行有效比較。")
        return

    # 4. 計算後續報酬
    # 計算未來 N 日的大盤報酬
    df[f'Future_Ret_{hold_days}d'] = df['TWII_Close'].shift(-hold_days) / df['TWII_Close'] - 1

    avg_ret_a = df.loc[group_a_mask, f'Future_Ret_{hold_days}d'].mean()
    avg_ret_b = df.loc[group_b_mask, f'Future_Ret_{hold_days}d'].mean()
    
    win_rate_a = (df.loc[group_a_mask, f'Future_Ret_{hold_days}d'] > 0).mean()
    win_rate_b = (df.loc[group_b_mask, f'Future_Ret_{hold_days}d'] > 0).mean()

    # 5. 輸出報告
    print(f"\n--- 策略 4 績效比較 (持有 {hold_days} 日) ---")
    print(f"Group A (真外資 - 台幣升值):")
    print(f"  平均報酬: {avg_ret_a:.2%}")
    print(f"  勝率: {win_rate_a:.2%}")
    
    print(f"\nGroup B (假外資 - 台幣貶值):")
    print(f"  平均報酬: {avg_ret_b:.2%}")
    print(f"  勝率: {win_rate_b:.2%}")

    # 6. 繪圖比較 (累積報酬)
    # 這裡我們模擬一個簡單的資金曲線：每次訊號出現就買入持有 N 天
    # 為了簡化，我們只畫出訊號點的平均報酬長條圖
    
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.figure(figsize=(10, 6))
    bars = plt.bar(['Group A (True Foreign)', 'Group B (False/Hedging)'], [avg_ret_a, avg_ret_b], color=['green', 'red'])
    plt.title(f'Strategy 4 Performance Comparison ({hold_days} Days Holding)')
    plt.ylabel('Average Return')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2%}',
                ha='center', va='bottom')

    plot_path = RESULTS_DIR / "strategy_forex_comparison.png"
    plt.savefig(plot_path)
    logging.info(f"比較圖表已儲存至 {plot_path}")

    # 儲存詳細數據
    detail_df = df.loc[foreign_buy_mask, ['TWII_Close', 'USDTWD_Close', 'USDTWD_Ret', f'Future_Ret_{hold_days}d']].copy()
    detail_df['Group'] = 'Neutral'
    detail_df.loc[group_a_mask, 'Group'] = 'Group A'
    detail_df.loc[group_b_mask, 'Group'] = 'Group B'
    
    csv_path = RESULTS_DIR / "strategy_forex_details.csv"
    detail_df.to_csv(csv_path, encoding='utf-8')
    logging.info(f"詳細數據已儲存至 {csv_path}")

def main():
    logging.info("--- 策略 4 流程開始 ---")
    try:
        master_dataset_path = PROCESSED_DATA_DIR / "master_dataset.csv"
        if not master_dataset_path.exists():
            logging.error("找不到主數據集，請先執行 clean_merge.py")
            return
            
        df = pd.read_csv(master_dataset_path, parse_dates=['Date'], index_col='Date', encoding='utf-8')
        run_backtest(df)
    except Exception as e:
        logging.error(f"執行失敗: {e}", exc_info=True)
    logging.info("--- 策略 4 流程結束 ---")

if __name__ == "__main__":
    main()
