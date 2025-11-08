import yfinance as yf
import os

# 定義常數
TICKER = "^GSPC"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"{TICKER.replace('^', '')}.parquet")

def download_gspc():
    """
    從 yfinance 下載 S&P 500 (^GSPC) 的歷史資料，並儲存為 Parquet 檔案。
    """
    # 確保輸出目錄存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 下載資料
    data = yf.download(TICKER, start="1990-01-01")

    # 儲存為 Parquet 格式
    data.to_parquet(OUTPUT_FILE)
    print(f"資料已成功下載並儲存至 {OUTPUT_FILE}")

if __name__ == '__main__':
    download_gspc()
