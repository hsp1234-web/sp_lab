"""
步驟 3：策略 1 (融資斷頭) 回測腳本
說明：
本腳本負責實現「策略1：融資斷頭抄底」的邏輯。
它會讀取處理過後的主數據集，根據策略條件篩選出交易訊號，
並進行簡單的回測，以評估策略的初步表現。

策略條件 (簡化版):
1. 融資餘額 (Margin_Balance_Value) 較前一日增加 > 50% (此條件目前無法觸發)。
2. 14日 RSI < 30。

執行方式：
uv run python scripts/03_strategy_margin.py
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
        logging.FileHandler('strategy_margin.log', mode='w')
    ]
)

# --- 全域設定 ---
PROCESSED_DATA_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# --- 主函式 ---

def run_backtest(df: pd.DataFrame, hold_days: list = [5, 10, 20]):
    """
    執行回測並計算績效。
    """
    logging.info("--- 開始執行策略回測 ---")

    # --- 1. 定義策略條件 ---
    # 條件 A: 融資餘額較前一日增加超過 50%
    # 注意：我們使用 .shift(1) 是為了確保我們在今天做決策時，只使用昨天的數據，避免未來函數 (look-ahead bias)
    cond_A = False
    if 'Margin_Balance_Value' in df.columns:
        logging.info("檢測到 'Margin_Balance_Value' 欄位，啟用融資餘額條件。")
        cond_A = df['Margin_Balance_Value'].pct_change(1).shift(1) > 0.5
    else:
        logging.warning("數據集中未找到 'Margin_Balance_Value' 欄位，融資餘額條件將不會被觸發。")

    # 條件 B: RSI < 30
    cond_B = df['RSI_14'].shift(1) < 30

    # 觸發訊號：同時滿足條件 A 和 B
    trigger_signals = df[cond_A & cond_B]

    if trigger_signals.empty:
        logging.warning("在給定的數據範圍內，沒有觸發任何交易訊號。")
        return

    logging.info(f"共觸發 {len(trigger_signals)} 次交易訊號。")
    print("觸發訊號的日期：")
    print(trigger_signals.index.to_list())

    # --- 2. 模擬回測與計算報酬 ---
    results = []
    for date in trigger_signals.index:
        result_row = {'trigger_date': date}
        for days in hold_days:
            # 計算未來 N 日的報酬率
            future_date = date + pd.Timedelta(days=days)
            # 找到實際的交易日 (如果未來日期是假日)
            if future_date in df.index:
                future_price = df.loc[future_date, 'TWII_Close']
                entry_price = df.loc[date, 'TWII_Close']
                ret = (future_price - entry_price) / entry_price
                result_row[f'ret_{days}d'] = ret
            else:
                result_row[f'ret_{days}d'] = None # 如果持有期間超出數據範圍
        results.append(result_row)

    results_df = pd.DataFrame(results).set_index('trigger_date')

    # --- 3. 計算並輸出績效指標 ---
    logging.info("--- 策略績效報告 ---")
    print(results_df.to_markdown())

    performance_summary = {}
    for days in hold_days:
        col_name = f'ret_{days}d'
        win_rate = (results_df[col_name] > 0).mean()
        avg_ret = results_df[col_name].mean()
        performance_summary[f'{days}d_WinRate'] = win_rate
        performance_summary[f'{days}d_AvgReturn'] = avg_ret
        print(f"\n持有 {days} 天績效:")
        print(f"  勝率: {win_rate:.2%}")
        print(f"  平均報酬率: {avg_ret:.2%}")

    # 儲存訊號與報酬
    signals_path = RESULTS_DIR / "strategy_margin_signals.csv"
    results_df.to_csv(signals_path)
    logging.info(f"詳細訊號與報酬已儲存至 {signals_path}")

    # --- 4. 繪製累積報酬圖 (以持有5天為例) ---
    if not results_df.empty and 'ret_5d' in results_df.columns:
        logging.info("正在繪製累積報酬圖...")
        plt.style.use('seaborn-v0_8-darkgrid')
        (1 + results_df['ret_5d']).cumprod().plot(figsize=(12, 6), title='策略1 (融資斷頭) - 累積報酬 (持有5日)')
        plt.ylabel('累積報酬')
        plt.xlabel('日期')
        plot_path = RESULTS_DIR / "strategy_margin_cumulative_return.png"
        plt.savefig(plot_path)
        plt.close()
        logging.info(f"累積報酬圖已儲存至 {plot_path}")


def main():
    """主執行函式"""
    logging.info("--- 策略 1 (融資斷頭) 回測流程開始 ---")

    try:
        # 讀取主數據集
        master_dataset_path = PROCESSED_DATA_DIR / "master_dataset.csv"
        df = pd.read_csv(master_dataset_path, parse_dates=['Date'], index_col='Date')
        logging.info(f"成功讀取主數據集，維度: {df.shape}")

        # 執行回測
        run_backtest(df)

    except FileNotFoundError:
        logging.error(f"錯誤：找不到主數據集 {master_dataset_path}。請先執行 02_clean_merge.py。")
    except Exception as e:
        logging.error(f"回測過程中發生未預期的錯誤: {e}", exc_info=True)

    logging.info("--- 策略 1 回測流程結束 ---")

if __name__ == "__main__":
    main()
