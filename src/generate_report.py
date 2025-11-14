import pandas as pd
import os

# 導入核心模組
from src.stats import calculate_backtest_stats
from src.viz import plot_equity_curve
from src.clean import clean_data # 需要用來獲取完整的價格數據
from src.fetch import download_gspc

# --- 全域設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 預設讀取完整版優化的結果
INPUT_DIR = os.path.join(BASE_DIR, 'output', 'wfo_results')
TRADE_LOG_PATH = os.path.join(INPUT_DIR, "final_wfo_trade_log.csv")

# 報告輸出的位置
REPORT_DIR = os.path.join(BASE_DIR, 'output', 'final_report')
EQUITY_CURVE_PATH = os.path.join(REPORT_DIR, 'final_equity_curve.jpg')

INITIAL_CAPITAL = 100000.0

def build_equity_curve_from_log(trade_log: pd.DataFrame, full_price_data: pd.DataFrame, initial_capital: float) -> pd.DataFrame:
    """
    根據交易日誌和完整的價格數據，重建每日的權益曲線。
    """
    # 確保索引是 datetime 類型
    trade_log['entry_date'] = pd.to_datetime(trade_log['entry_date'])
    trade_log['exit_date'] = pd.to_datetime(trade_log['exit_date'])

    # 建立一個與完整價格數據對齊的權益 DataFrame
    equity_curve = pd.DataFrame(index=full_price_data.index, columns=['equity'])
    equity_curve['equity'] = initial_capital # 初始化

    # 將已實現的損益累加到對應的日期
    realized_pnl_by_date = trade_log.groupby('exit_date')['pnl'].sum().cumsum()
    equity_curve['realized_pnl'] = realized_pnl_by_date.reindex(equity_curve.index, method='ffill').fillna(0)

    # 計算未實現損益 (較為複雜，這裡我們先用簡化版，只考慮已實現損益)
    # 在一個更完整的實現中，需要追蹤每日的持倉來計算未實現損益
    equity_curve['equity'] += equity_curve['realized_pnl']

    return equity_curve

def main():
    """
    讀取 WFO 的交易日誌，計算最終績效並產生報告。
    """
    print("--- 開始生成最終績效報告 ---")
    os.makedirs(REPORT_DIR, exist_ok=True)

    # --- 1. 檢查交易日誌是否存在 ---
    if not os.path.exists(TRADE_LOG_PATH):
        print(f"錯誤：找不到交易日誌檔案 '{TRADE_LOG_PATH}'。")
        print("請先成功執行一次 `run_optimization.py` 來產生此檔案。")
        # 嘗試讀取驗證模式的日誌作為備用
        verification_log_path = os.path.join(BASE_DIR, 'output', 'wfo_results_verification', 'verification_trade_log.csv')
        if os.path.exists(verification_log_path):
            print(f"找到驗證模式的日誌，將使用 '{verification_log_path}' 進行報告生成。")
            trade_log_df = pd.read_csv(verification_log_path)
        else:
            return
    else:
        trade_log_df = pd.read_csv(TRADE_LOG_PATH)

    if trade_log_df.empty:
        print("交易日誌是空的，無法生成報告。")
        return

    print(f"成功讀取 {len(trade_log_df)} 筆交易紀錄。")

    # --- 2. 準備完整的價格數據以重建權益曲線 ---
    # 我們需要完整的歷史數據來建立一個連續的權益曲線時間軸
    print("正在準備完整的歷史價格數據...")
    raw_df = download_gspc() # 假設 download_gspc 能直接返回 DataFrame
    clean_df = clean_data(raw_df)

    # --- 3. 重建權益曲線 ---
    print("正在根據交易日誌重建權益曲線...")
    equity_curve = build_equity_curve_from_log(trade_log_df, clean_df, INITIAL_CAPITAL)

    # --- 4. 計算最終績效指標 ---
    print("正在計算最終的樣本外績效指標...")
    final_stats = calculate_backtest_stats(
        trade_log=trade_log_df,
        equity_curve=equity_curve,
        initial_capital=INITIAL_CAPITAL
    )

    # --- 5. 產生視覺化圖表並顯示結果 ---
    print("正在產生最終的權益曲線圖...")
    plot_equity_curve(equity_curve, EQUITY_CURVE_PATH, final_stats)

    print("\n========= 最終樣本外績效報告 =========\n")
    for metric, value in final_stats.items():
        if isinstance(value, float):
            print(f"{metric:<20}: {value:.4f}")
        else:
            print(f"{metric:<20}: {value}")
    print("\n======================================\n")
    print(f"報告生成完畢！最終權益曲線圖已儲存至: {EQUITY_CURVE_PATH}")

if __name__ == '__main__':
    main()
