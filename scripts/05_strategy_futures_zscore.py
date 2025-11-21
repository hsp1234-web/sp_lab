"""
步驟 5：策略 2 (期貨 Z-Score) 回測腳本
說明：
本腳本負責實現「策略2：期貨 Z-Score 均值回歸」的邏輯。
(此策略未在原計畫書詳述，根據常見量化邏輯推演實作)

策略邏輯:
1. 計算大盤 (或期貨) 的 Z-Score (乖離率標準化)。
   Z-Score = (Close - MA_60) / Std_60
2. 進場訊號:
   - Long: Z-Score < -2 (超跌，預期反彈)
   - Short: Z-Score > 2 (超漲，預期回檔) - *本腳本主要測試做多*
3. 出場訊號:
   - Z-Score 回歸到 0 或持有固定天數。

執行方式：
uv run python scripts/05_strategy_futures_zscore.py
"""

import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('strategy_zscore.log', mode='w', encoding='utf-8')
    ]
)

PROCESSED_DATA_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_backtest(df: pd.DataFrame):
    logging.info("--- 開始執行策略 2 (Z-Score) 回測 ---")

    if 'Z_Score' not in df.columns:
        logging.warning("數據集中未找到 'Z_Score'，嘗試重新計算...")
        # 簡單補算 Z-Score (若 clean_merge.py 未產出)
        window = 60
        roll = df['TWII_Close'].rolling(window)
        df['Z_Score'] = (df['TWII_Close'] - roll.mean()) / roll.std()

    # 策略參數
    entry_threshold = -2.0
    exit_threshold = 0.0
    
    # 產生訊號
    # 1. 進場: Z-Score 低於 -2
    long_signals = (df['Z_Score'] < entry_threshold) & (df['Z_Score'].shift(1) >= entry_threshold)
    
    logging.info(f"Z-Score < {entry_threshold} 進場訊號次數: {long_signals.sum()}")

    if long_signals.sum() == 0:
        logging.warning("無觸發訊號。")
        return

    # 簡單回測：買進後持有直到 Z-Score > 0 或持有 20 天
    trades = []
    for date in df[long_signals].index:
        entry_price = df.loc[date, 'TWII_Close']
        
        # 尋找出場點 (未來日期)
        future_data = df.loc[date:].iloc[1:] # 從明天開始找
        exit_date = None
        exit_price = None
        reason = None
        
        for d, row in future_data.iterrows():
            # 出場條件 1: Z-Score 回歸 0
            if row['Z_Score'] > exit_threshold:
                exit_date = d
                exit_price = row['TWII_Close']
                reason = 'Mean Reversion'
                break
            
            # 出場條件 2: 強制停損/停利 (持有超過 20 天)
            if (d - date).days > 20:
                exit_date = d
                exit_price = row['TWII_Close']
                reason = 'Time Stop'
                break
        
        if exit_date:
            ret = (exit_price - entry_price) / entry_price
            trades.append({
                'Entry_Date': date,
                'Exit_Date': exit_date,
                'Entry_Price': entry_price,
                'Exit_Price': exit_price,
                'Return': ret,
                'Reason': reason
            })

    # 績效統計
    if not trades:
        logging.info("無完成之交易。")
        return

    trades_df = pd.DataFrame(trades)
    avg_ret = trades_df['Return'].mean()
    win_rate = (trades_df['Return'] > 0).mean()
    
    print(f"\n--- 策略 2 (Z-Score) 績效報告 ---")
    print(f"總交易次數: {len(trades_df)}")
    print(f"平均報酬: {avg_ret:.2%}")
    print(f"勝率: {win_rate:.2%}")
    print(trades_df.head().to_markdown())

    # 儲存
    csv_path = RESULTS_DIR / "strategy_zscore_trades.csv"
    trades_df.to_csv(csv_path, encoding='utf-8')
    logging.info(f"交易明細已儲存至 {csv_path}")

    # 繪圖
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['Z_Score'], label='Z-Score', color='gray', alpha=0.5)
    plt.axhline(entry_threshold, color='green', linestyle='--', label='Buy Threshold')
    plt.axhline(exit_threshold, color='black', linestyle='-', label='Mean')
    
    # 標示買點
    buy_dates = trades_df['Entry_Date']
    buy_zscores = df.loc[buy_dates, 'Z_Score']
    plt.scatter(buy_dates, buy_zscores, color='red', marker='^', label='Buy Signal')
    
    plt.title('Strategy 2: Z-Score Signals')
    plt.legend()
    plot_path = RESULTS_DIR / "strategy_zscore_chart.png"
    plt.savefig(plot_path)
    logging.info(f"訊號圖已儲存至 {plot_path}")

def main():
    logging.info("--- 策略 2 流程開始 ---")
    try:
        master_dataset_path = PROCESSED_DATA_DIR / "master_dataset.csv"
        if not master_dataset_path.exists():
            logging.error("找不到主數據集")
            return
        df = pd.read_csv(master_dataset_path, parse_dates=['Date'], index_col='Date', encoding='utf-8')
        run_backtest(df)
    except Exception as e:
        logging.error(f"執行失敗: {e}", exc_info=True)
    logging.info("--- 策略 2 流程結束 ---")

if __name__ == "__main__":
    main()
