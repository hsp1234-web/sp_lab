import yfinance as yf
import os
import pandas as pd

# --- 新的、更通用的函數 ---
def fetch_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    從 yfinance 下載指定 ticker 的歷史資料。

    Args:
        ticker (str): 要下載的股票/指數代碼 (例如 "^GSPC")。
        start_date (str): 開始日期，格式 "YYYY-MM-DD"。
        end_date (str): 結束日期，格式 "YYYY-MM-DD"。

    Returns:
        pd.DataFrame: 包含 OHLCV 數據的 DataFrame，索引為日期。
    """
    print(f"正在從 yfinance 下載 {ticker} 的數據，從 {start_date} 到 {end_date}...")
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        raise ValueError(f"錯誤：找不到 {ticker} 的數據。請檢查 ticker 是否正確。")
    print("下載完成。")
    return data

# --- 舊的函數 (保留但不再是主要接口) ---
TICKER_LEGACY = "^GSPC"
OUTPUT_DIR_LEGACY = "data/raw"
OUTPUT_FILE_LEGACY = os.path.join(OUTPUT_DIR_LEGACY, f"{TICKER_LEGACY.replace('^', '')}.parquet")

def download_gspc():
    """
    (舊版) 從 yfinance 下載 S&P 500 (^GSPC) 的歷史資料，並儲存為 Parquet 檔案。
    """
    # 確保輸出目錄存在
    os.makedirs(OUTPUT_DIR_LEGACY, exist_ok=True)

    # 下載資料
    data = yf.download(TICKER_LEGACY, start="1990-01-01")

    # 儲存為 Parquet 格式
    data.to_parquet(OUTPUT_FILE_LEGACY)
    print(f"資料已成功下載並儲存至 {OUTPUT_FILE_LEGACY}")

if __name__ == '__main__':
    # 當直接執行此檔案時，執行舊的下載邏輯
    download_gspc()
