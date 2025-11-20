"""
步驟 1：數據獲取腳本
說明：
本腳本負責從外部 API 和網站獲取研究所需的原始數據，
並將其儲存至 `data/raw/` 資料夾中，以供後續步驟使用。

功能：
1. 使用 twstock 下載台股指數的替代數據 (TSMC '2330')。
2. 使用 FRED API 下載美元兌新台幣 (USDTWD) 的歷史匯率數據。
3. 爬取台灣證券交易所的融資維持率數據。

執行方式：
在執行前，請先設定您的 FRED API 金鑰：
export FRED_API_KEY='您的金鑰'

然後執行腳本：
uv run python scripts/01_fetch_data.py --start 2022-01-01 --end 2025-11-21
"""

import argparse
import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
import twstock
from fredapi import Fred

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fetch_data.log', mode='w')
    ]
)

# --- 全域設定 ---
RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# --- 函式定義 ---

def fetch_twii_data_with_twstock(start_date, end_date):
    """使用 twstock 下載台積電 (2330) 作為大盤指數的替代數據。"""
    logging.info("開始使用 twstock 下載台股數據 (2330)...")
    try:
        stock = twstock.Stock('2330')
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        all_data = []
        # 逐月獲取數據
        current_dt = start_dt
        while current_dt <= end_dt:
            logging.info(f"正在獲取 {current_dt.year}-{current_dt.month} 的數據...")
            monthly_data = stock.fetch(current_dt.year, current_dt.month)
            if monthly_data:
                all_data.extend(monthly_data)
            time.sleep(2) # 遵守 API 禮儀
            current_dt = current_dt + pd.DateOffset(months=1)

        if not all_data:
            raise ValueError("使用 twstock 未獲取到任何數據。")

        df = pd.DataFrame(all_data)
        df = df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'capacity': 'Volume'})
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
        df = df[~df.index.duplicated(keep='first')] # 移除重複的索引
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]

        output_path = RAW_DATA_DIR / "TWII.csv"
        df.to_csv(output_path)
        logging.info(f"成功將台股數據儲存至 {output_path}")
        return True
    except Exception as e:
        logging.error(f"使用 twstock 下載數據時發生錯誤: {e}", exc_info=True)
        return False

def fetch_forex_data_with_fred(start_date, end_date):
    """使用 FRED API 下載美元兌台幣匯率數據 (DEXTWUS)。"""
    logging.info("開始使用 FRED API 下載 USDTWD 匯率數據...")
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        logging.error("錯誤：請設定 FRED_API_KEY 環境變數。")
        return False

    try:
        fred = Fred(api_key=api_key)
        # 'DEXTWUS' 是 FRED 中代表「美元兌新台幣」的序列 ID
        rates_series = fred.get_series('DEXTWUS', observation_start=start_date, observation_end=end_date)

        if rates_series.empty:
            raise ValueError("從 FRED API 未獲取到任何匯率數據。")

        rates_df = pd.DataFrame({'Close': rates_series})
        rates_df.index.name = 'Date'
        rates_df = rates_df.dropna() # FRED 可能會返回 NaN 值

        # 為了與其他數據格式對齊，增加 OHLC 欄位
        rates_df['Open'] = rates_df['Close']
        rates_df['High'] = rates_df['Close']
        rates_df['Low'] = rates_df['Close']
        rates_df['Volume'] = 0
        rates_df = rates_df[['Open', 'High', 'Low', 'Close', 'Volume']]

        output_path = RAW_DATA_DIR / "USDTWD.csv"
        rates_df.to_csv(output_path)
        logging.info(f"成功將 USDTWD 匯率數據從 FRED 儲存至 {output_path}")
        return True
    except Exception as e:
        logging.error(f"使用 FRED API 獲取數據時發生錯誤: {e}", exc_info=True)
        return False

def fetch_twse_margin_data(start_date, end_date):
    """分日爬取台灣證券交易所的融資維持率數據。"""
    logging.info("開始爬取融資維持率數據...")
    all_data = []
    date_range = pd.to_datetime(pd.date_range(start=start_date, end=end_date, freq='D'))

    for date in date_range:
        # 只在週一到週五查詢
        if date.weekday() >= 5:
            continue

        url = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date={date.strftime('%Y%m%d')}&selectType=DR"
        logging.info(f"正在爬取日期: {date.strftime('%Y-%m-%d')}...")
        try:
            response = requests.get(url, headers=REQUEST_HEADERS)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data or not data.get('data'):
                logging.warning(f"日期 {date.strftime('%Y-%m-%d')} 沒有數據。")
                continue

            # DR 格式通常只有一筆或少量數據
            for row in data['data']:
                try:
                    # '112/11/20' -> '2023-11-20'
                    roc_date_parts = row[0].strip().split('/')
                    ad_year = int(roc_date_parts[0]) + 1911
                    ad_date = f"{ad_year}-{int(roc_date_parts[1]):02d}-{int(roc_date_parts[2]):02d}"

                    # 檢查日期是否一致
                    if ad_date != date.strftime('%Y-%m-%d'):
                        logging.warning(f"回傳日期 {ad_date} 與查詢日期 {date.strftime('%Y-%m-%d')} 不符，跳過。")
                        continue

                    all_data.append({
                        'Date': ad_date,
                        'Margin_Purchase_Value': int(row[1].replace(',', '')),
                        'Margin_Sale_Value': int(row[2].replace(',', '')),
                        'Margin_Balance_Value': int(row[4].replace(',', '')),
                        'Margin_Maintenance_Ratio': float(row[6].replace(',', ''))
                    })
                except (ValueError, IndexError) as e:
                    logging.warning(f"無法解析此行數據: {row}，錯誤: {e}")
                    continue
        except requests.exceptions.RequestException as e:
            logging.error(f"爬取 {date.strftime('%Y-%m-%d')} 數據時網路錯誤: {e}")
            # 不中止，繼續下一天
        except Exception as e:
            logging.error(f"處理 {date.strftime('%Y-%m-%d')} 數據時發生錯誤: {e}", exc_info=True)

        time.sleep(5) # 由於是逐日查詢，必須拉長延遲時間

    if not all_data:
        logging.error("未成功爬取到任何融資維持率數據。")
        return False

    df = pd.DataFrame(all_data)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date').set_index('Date')

    output_path = RAW_DATA_DIR / "margin_data.csv"
    df.to_csv(output_path)
    logging.info(f"成功將融資維持率數據儲存至 {output_path}")
    return True

def main():
    """主執行函式"""
    parser = argparse.ArgumentParser(description="量化研究專案 - 數據獲取模組")
    parser.add_argument("--start", type=str, required=True, help="數據下載開始日期 (格式: YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="數據下載結束日期 (格式: YYYY-MM-DD)")
    args = parser.parse_args()

    logging.info("--- 數據獲取流程開始 ---")

    # 步驟 1: 下載台股數據
    if not fetch_twii_data_with_twstock(args.start, args.end):
        logging.error("台股數據下載失敗，流程中止。")
        return

    # 步驟 2: 下載匯率數據
    if not fetch_forex_data_with_fred(args.start, args.end):
        logging.error("匯率數據下載失敗，流程中止。")
        return

    # 步驟 3: 爬取融資維持率數據
    if not fetch_twse_margin_data(args.start, args.end):
        logging.error("融資維持率數據爬取失敗，流程中止。")
        return

    logging.info("--- 所有數據獲取流程成功結束 ---")

if __name__ == "__main__":
    main()
