import pandas as pd
import os
from tqdm import tqdm

# 導入我們建立的核心組件
from src.clean import clean_data
from src.fetch import download_gspc
from src.optimizer_utils import create_walk_forward_splits
from src.optimizer import run_ga_optimization
from src.feat import calculate_features
from src.sp_signal import generate_signals
from src.backtest import run_backtest
from src.stats import calculate_backtest_stats
from src.viz import plot_equity_curve

# --- 全域設定 (快速驗證模式) ---
# 路徑管理
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw', 'wfo_raw.parquet')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'wfo_results_verification') # 使用獨立的輸出資料夾

# 滾動優化參數 (已大幅縮減以進行快速驗證)
TRAIN_PERIOD_YEARS = 1   # 訓練期: 1 年
TEST_PERIOD_YEARS = 0.25 # 測試期: 3 個月
STEP_YEARS = 0.25        # 滾動步長: 3 個月
DAYS_PER_YEAR = 252

# 基因演算法參數 (已大幅縮減以進行快速驗證)
POP_SIZE = 10 # 族群大小
NGEN = 5      # 世代數
CXPB = 0.5
MUTPB = 0.2

def main():
    """
    執行快速的「驗證模式」滾動前向優化流程。
    """
    print("--- [步驟 1/4] 正在準備數據 ---")
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    download_gspc(RAW_DATA_PATH)
    raw_df = pd.read_parquet(RAW_DATA_PATH)
    clean_df = clean_data(raw_df)
    print("數據準備完成。")

    print("\n--- [步驟 2/4] 正在建立滾動數據分割 (快速驗證模式) ---")
    train_len = int(TRAIN_PERIOD_YEARS * DAYS_PER_YEAR)
    test_len = int(TEST_PERIOD_YEARS * DAYS_PER_YEAR)
    step_len = int(STEP_YEARS * DAYS_PER_YEAR)

    # 為了確保驗證能運行，我們只取最近的幾年數據
    recent_data = clean_df.last('5Y')

    wfo_splits = list(create_walk_forward_splits(
        data=recent_data,
        train_period_len=train_len,
        test_period_len=test_len,
        step=step_len
    ))
    print(f"成功建立 {len(wfo_splits)} 個滾動窗口。")

    print("\n--- [步驟 3/4] 正在執行滾動前向優化 (快速驗證模式) ---")
    all_oos_trade_logs = []

    for i, (train_set, test_set) in enumerate(tqdm(wfo_splits, desc="滾動窗口進度")):
        print(f"\n--- 窗口 {i+1}/{len(wfo_splits)} ---")
        print(f"訓練期: {train_set.index.min().date()} to {train_set.index.max().date()}")

        best_params = run_ga_optimization(
            training_data=train_set,
            pop_size=POP_SIZE,
            ngen=NGEN,
            cxpb=CXPB,
            mutpb=MUTPB
        )
        print(f"訓練完成，找到的最佳參數: {best_params}")

        print(f"測試期: {test_set.index.min().date()} to {test_set.index.max().date()}")
        atr_period, atr_multiplier, high_vol_trend = best_params[0], best_params[1], best_params[2]

        features_oos = calculate_features(test_set, atr_period=int(atr_period))
        signals_oos = generate_signals(
            features_oos,
            high_vol_trend=high_vol_trend,
            atr_period=int(atr_period),
            atr_multiplier=atr_multiplier
        )
        trade_log_oos, _ = run_backtest(
            price_data=test_set,
            signals=signals_oos['signal'],
            init_cap=100000.0,
            pos_size=1
        )

        print(f"測試完成，產生了 {len(trade_log_oos)} 筆樣本外交易。")
        all_oos_trade_logs.append(trade_log_oos)

    print("\n--- [步驟 4/4] 正在匯總並儲存最終結果 ---")
    if all_oos_trade_logs:
        final_trade_log = pd.concat(all_oos_trade_logs, ignore_index=True)
        final_log_path = os.path.join(OUTPUT_DIR, "verification_trade_log.csv")
        final_trade_log.to_csv(final_log_path, index=False)
        print(f"快速驗證流程執行完畢！")
        print(f"最終的樣本外交易日誌已儲存至: {final_log_path}")
    else:
        print("快速驗證流程執行完畢，但未產生任何交易。")

if __name__ == '__main__':
    main()
