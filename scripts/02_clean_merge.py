"""
步驟 2：數據清洗與合併腳本
說明：
本腳本負責讀取 `data/raw/` 中的原始數據，進行清洗、合併，
並計算策略所需的衍生技術指標（如 RSI），
最終產出一個乾淨、統一的主數據集 `master_dataset.csv`。

功能：
1. 讀取台股、匯率及融資數據。
2. 將多個數據源按日期對齊合併。
3. 處理缺失值。
4. 手動計算 RSI 指標。
5. 儲存處理過的數據集至 `data/processed/`。

執行方式：
uv run python scripts/02_clean_merge.py
"""

import logging
from pathlib import Path

import pandas as pd

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('clean_merge.log', mode='w')
    ]
)

# --- 全域設定 ---
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- 輔助函式 ---
def calculate_rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """
    手動計算相對強弱指數 (RSI)。

    Args:
        series (pd.Series): 收盤價序列。
        length (int): RSI 的計算週期，預設為 14。

    Returns:
        pd.Series: RSI 值序列。
    """
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/length, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/length, adjust=False).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- 主函式 ---

def main():
    """主執行函式"""
    logging.info("--- 數據清洗與合併流程開始 ---")

    try:
        # --- 1. 讀取原始數據 ---
        logging.info("讀取原始 CSV 檔案...")
        twii_df = pd.read_csv(RAW_DATA_DIR / "TWII.csv", parse_dates=['Date'], index_col='Date', encoding='utf-8')
        usdtwd_df = pd.read_csv(RAW_DATA_DIR / "USDTWD.csv", parse_dates=['Date'], index_col='Date', encoding='utf-8')

        # 融資數據可能是空的，需要做例外處理
        margin_path = RAW_DATA_DIR / "margin_data.csv"
        if margin_path.exists() and margin_path.stat().st_size > 0:
             margin_df = pd.read_csv(margin_path, parse_dates=['Date'], index_col='Date', encoding='utf-8')
             # 只保留我們需要的欄位
             margin_df = margin_df[['Margin_Balance_Value', 'Margin_Maintenance_Ratio']]
        else:
            logging.warning("margin_data.csv 為空或不存在，將創建一個空的 DataFrame。")
            margin_df = pd.DataFrame()

        # 新增：讀取三大法人數據
        investors_path = RAW_DATA_DIR / "institutional_investors.csv"
        if investors_path.exists() and investors_path.stat().st_size > 0:
            investors_df = pd.read_csv(investors_path, parse_dates=['date'], encoding='utf-8')
            # 將 'date' 欄位設為索引並重新命名
            investors_df = investors_df.rename(columns={'date': 'Date'}).set_index('Date')
        else:
            logging.warning("institutional_investors.csv 為空或不存在，將創建一個空的 DataFrame。")
            investors_df = pd.DataFrame()


        # --- 2. 重新命名欄位以避免合併衝突 ---
        twii_df = twii_df.rename(columns={
            'Open': 'TWII_Open', 'High': 'TWII_High', 'Low': 'TWII_Low', 'Close': 'TWII_Close', 'Volume': 'TWII_Volume'
        })
        usdtwd_df = usdtwd_df.rename(columns={'Close': 'USDTWD_Close'})
        # 我們只需要匯率的收盤價
        usdtwd_df = usdtwd_df[['USDTWD_Close']]

        # --- 3. 數據前處理與合併 ---
        logging.info("合併多個數據源...")

        # --- 3a. 處理三大法人數據 ---
        if not investors_df.empty:
            logging.info("處理三大法人數據...")
            # 計算淨買超 = 買超 - 賣超 (單位: 股)
            investors_df['net_buy'] = investors_df['buy'] - investors_df['sell']

            # 使用 pivot_table 將 name 欄位的類別轉換為欄位
            investors_pivot_df = investors_df.pivot_table(
                index=investors_df.index,
                columns='name',
                values='net_buy'
            )

            # 重新命名欄位，使其更具描述性
            investors_pivot_df = investors_pivot_df.rename(columns={
                'Foreign_Investor': 'Inst_Foreign_Net_Buy',
                'Investment_Trust': 'Inst_Trust_Net_Buy',
                'Dealer_self': 'Inst_Dealer_Self_Net_Buy',
                'Dealer_Hedging': 'Inst_Dealer_Hedge_Net_Buy',
                'Foreign_Dealer_Self': 'Inst_Foreign_Dealer_Net_Buy'
            })

            # 加總三大法人淨買超 (外資 + 投信 + 自營商)
            # 自營商包含避險和自行買賣
            # 使用 .get() 處理可能不存在的欄位，預設為 0
            inst_columns = investors_pivot_df.columns
            foreign_cols = [col for col in inst_columns if 'Foreign' in col]
            trust_cols = [col for col in inst_columns if 'Trust' in col]
            dealer_cols = [col for col in inst_columns if 'Dealer' in col]

            investors_pivot_df['Inst_Total_Net_Buy'] = \
                investors_pivot_df[foreign_cols].sum(axis=1) + \
                investors_pivot_df[trust_cols].sum(axis=1) + \
                investors_pivot_df[dealer_cols].sum(axis=1)

        # --- 3b. 合併主要數據 ---
        # 將台股與匯率數據外連接合併
        master_df = pd.concat([twii_df, usdtwd_df], axis=1, join='outer')

        # 如果融資數據存在，再將其合併進來
        if not margin_df.empty:
            master_df = pd.concat([master_df, margin_df], axis=1, join='outer')

        # 如果法人數據存在，也合併進來
        if 'investors_pivot_df' in locals() and not investors_pivot_df.empty:
            master_df = pd.concat([master_df, investors_pivot_df], axis=1, join='outer')

        # 按日期排序
        master_df = master_df.sort_index()

        # --- 4. 處理缺失值 ---
        logging.info("使用 'ffill' 填補缺失值...")
        # 某些交易日可能只有部分數據（如假日），使用 ffill 向前填充是合理的做法
        master_df.fillna(method='ffill', inplace=True)

        # 如果填充後開頭仍有 NaN（例如，數據的最開始幾天就缺失），則直接移除這些行
        master_df.dropna(inplace=True)

        if master_df.empty:
            raise ValueError("數據合併與清洗後，DataFrame 為空，請檢查原始數據。")

        # --- 5. 計算技術指標 ---
        logging.info("計算 RSI(14) 指標...")
        master_df['RSI_14'] = calculate_rsi(master_df['TWII_Close'], length=14)

        # 計算完成後，再次處理可能因指標計算產生的 NaN 值
        master_df.dropna(inplace=True)

        # --- 6. 儲存處理完成的數據集 ---
        output_path = PROCESSED_DATA_DIR / "master_dataset.csv"
        master_df.to_csv(output_path, encoding='utf-8')
        logging.info(f"成功將主數據集儲存至 {output_path}")
        logging.info(f"數據集維度: {master_df.shape}")
        logging.info("主數據集預覽 (前五行):")
        print(master_df.head())


    except FileNotFoundError as e:
        logging.error(f"數據讀取錯誤：找不到檔案 {e.filename}。請先執行 01_fetch_data.py。")
    except Exception as e:
        logging.error(f"處理過程中發生未預期的錯誤: {e}", exc_info=True)

    logging.info("--- 數據清洗與合併流程結束 ---")

if __name__ == "__main__":
    main()
