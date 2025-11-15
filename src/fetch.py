import yfinance as yf
import os

# 定義常數
TICKER = "^GSPC"

def download_gspc(output_path: str):
    """
    從 yfinance 下載 S&P 500 (^GSPC) 的歷史資料，並儲存為 Parquet 檔案。

    Args:
        output_path (str): 儲存 Parquet 檔案的完整路徑。
    """
    # 確保輸出目錄存在
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # 下載資料
    data = yf.download(TICKER, start="1990-01-01", auto_adjust=True)

    # 儲存為 Parquet 格式
    data.to_parquet(output_path)
    print(f"資料已成功下載並儲存至 {output_path}")

if __name__ == '__main__':
    # 為了方便獨立執行此腳本，我們在此處定義一個預設的輸出路徑。
    # 這段程式碼只有在 `python src/fetch.py` 被直接執行時才會觸發。
    DEFAULT_OUTPUT_DIR = "data/raw"
    DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, f"{TICKER.replace('^', '')}.parquet")
    download_gspc(DEFAULT_OUTPUT_FILE)
