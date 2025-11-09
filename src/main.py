# -*- coding: utf-8 -*-
"""
主執行腳本 (Orchestrator)

這個腳本是整個量化研究專案的單一進入點。它會按照正確的順序，
依序執行從數據獲取、清洗、特徵工程、統計分析、訊號生成、
回測模擬，到最終視覺化報告產出的完整流程。

設計這個主腳本的目的，是為了讓整個複雜的流程可以被一鍵觸發，
特別是在像 Google Colab 這樣的遠端環境中，能確保流程的
一致性與可重現性。
"""

import os
import pandas as pd
from IPython.display import Image, display

# ----------------------------------------------------------------------------
# 核心模組導入
# ----------------------------------------------------------------------------
# 這裡我們從各個獨立的 .py 檔案中，導入它們最核心的功能函式。
# 這種設計讓我們的 `main.py` 變得非常簡潔，只負責流程的「編排」，
# 而不涉及具體的實作細節。

from fetch import download_gspc
from clean import clean_gspc_data
from feat import calculate_features
from stats import run_volatility_analysis
from signal import generate_signals, adjust_signals_for_execution
from backtest import run_backtest
from cost import calculate_simple_cost
from viz import plot_equity_curve, calculate_performance_metrics

# ----------------------------------------------------------------------------
# 全域設定與路徑管理
# ----------------------------------------------------------------------------
# 我們將所有會用到的檔案路徑和重要的回測參數，統一在這裡進行管理。
# 這樣做的好處是，未來如果需要調整檔案儲存位置或修改回測設定，
# 只需在這個區塊進行修改即可，無需改動下方的執行流程。

# --- 路徑設定 ---
# 建立一個相對於目前腳本位置的 `data` 和 `output` 資料夾路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data') # 退回到專案根目錄，再進入 data
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw', 'gspc_raw.parquet')
CLEAN_DATA_PATH = os.path.join(DATA_DIR, 'processed', 'gspc_clean.parquet')
FEATURES_PATH = os.path.join(DATA_DIR, 'processed', 'features.parquet')
SIGNALS_PATH = os.path.join(DATA_DIR, 'processed', 'signals.parquet')

OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
EQUITY_CURVE_PATH = os.path.join(OUTPUT_DIR, 'equity_curve.jpg')
TRADE_LOG_PATH = os.path.join(OUTPUT_DIR, 'trade_log.csv')

# --- 回測參數 ---
INIT_CAPITAL = 100000.0  # 初始資金
POS_SIZE = 100          # 每次交易的部位大小
COST_PARAMS = {         # 交易成本參數
    'fee_per_trade': 1.5, # 每筆交易固定手續費
    'slippage_pct': 0.0001 # 滑價成本 (百分比)
}

def ensure_directories_exist():
    """
    確保所有需要的數據和輸出資料夾都存在，如果不存在則自動建立。
    """
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(CLEAN_DATA_PATH), exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("✅ 資料夾結構已確認。")

# ----------------------------------------------------------------------------
# 主流程執行函式
# ----------------------------------------------------------------------------
def main():
    """
    執行完整的端到端 (End-to-End) 量化研究與回測流程。
    """
    # --- 步驟 0: 環境準備 ---
    print("--- [ 步驟 0/7 ] 正在準備執行環境 ---")
    ensure_directories_exist()
    print("-" * 40)

    # --- 步驟 1: 數據獲取 ---
    print("--- [ 步驟 1/7 ] 正在下載原始市場數據 ---")
    download_gspc(RAW_DATA_PATH)
    print("✅ 原始數據下載完成。")
    print("-" * 40)

    # --- 步驟 2: 數據清洗 ---
    print("--- [ 步驟 2/7 ] 正在進行數據清洗 ---")
    raw_df = pd.read_parquet(RAW_DATA_PATH)
    clean_df = clean_gspc_data(raw_df)
    clean_df.to_parquet(CLEAN_DATA_PATH)
    print(f"✅ 數據清洗完成，已儲存至 {CLEAN_DATA_PATH}")
    print("-" * 40)

    # --- 步驟 3: 特徵工程 ---
    print("--- [ 步驟 3/7 ] 正在計算技術指標特徵 ---")
    features_df = calculate_features(clean_df)
    features_df.to_parquet(FEATURES_PATH)
    print(f"✅ 特徵計算完成，已儲存至 {FEATURES_PATH}")
    print("-" * 40)

    # --- 步驟 4: 統計分析與訊號生成 ---
    # 在這個專案中，`stats` 模組主要是為了研究與驗證，其結論
    # 已經被直接應用在 `signal` 模組中。因此，在自動化流程裡，
    # 我們可以直接生成訊號。
    print("--- [ 步驟 4/7 ] 正在生成交易訊號 ---")
    ideal_signals = generate_signals(features_df)
    # 考量到非交易日，對理想訊號進行延遲與取消的調整
    executable_signals = adjust_signals_for_execution(ideal_signals, features_df['is_trading_day'])

    # 將訊號與價格數據對齊，方便回測模組使用
    signals_df = pd.DataFrame({
        'price': features_df['Close'],
        'signal': executable_signals
    }).ffill()
    signals_df.to_parquet(SIGNALS_PATH)
    print(f"✅ 交易訊號生成完成，已儲存至 {SIGNALS_PATH}")
    print("-" * 40)

    # --- 步驟 5: 執行回測 ---
    print("--- [ 步驟 5/7 ] 正在執行回測模擬 (包含交易成本) ---")
    trade_log, equity_curve = run_backtest(
        price_data=features_df,
        signals=signals_df['signal'],
        init_cap=INIT_CAPITAL,
        pos_size=POS_SIZE,
        cost_mode='simple', # 指定使用 'simple' 成本模型
        cost_params=COST_PARAMS
    )
    trade_log.to_csv(TRADE_LOG_PATH)
    print(f"✅ 回測執行完畢，交易日誌已儲存至 {TRADE_LOG_PATH}")
    print("-" * 40)

    # --- 步驟 6: 績效計算與視覺化 ---
    print("--- [ 步驟 6/7 ] 正在計算績效指標並產生視覺化圖表 ---")
    performance_metrics = calculate_performance_metrics(equity_curve)
    plot_equity_curve(equity_curve, EQUITY_CURVE_PATH, performance_metrics)
    print(f"✅ 權益曲線圖已儲存至 {EQUITY_CURVE_PATH}")
    print("-" * 40)

    # --- 步驟 7: 顯示最終結果 ---
    print("--- [ 步驟 7/7 ] 正在顯示最終績效報告 ---")
    print("\n========= 最終績效報告 =========\n")
    for metric, value in performance_metrics.items():
        print(f"{metric:<20}: {value:.4f}")
    print("\n==================================\n")

    # 在 Colab 環境中，可以直接顯示圖片
    # (這段程式碼在本地執行時不會報錯，只是不會顯示圖片)
    try:
        print("正在嘗試顯示權益曲線圖...")
        display(Image(filename=EQUITY_CURVE_PATH))
    except NameError:
        print(" (在非 IPython 環境中，請手動開啟圖片檔案檢視)")
    except Exception as e:
        print(f"無法顯示圖片: {e}")

# ----------------------------------------------------------------------------
# 程式進入點
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # 這行是 Python 的一個標準寫法。
    # 它確保了 `main()` 這個函式只有在 `python main.py` 被直接執行時才會被呼叫。
    # 如果這個檔案被其他 .py 檔案作為模組導入 (import) 時，`main()` 則不會執行。
    main()
