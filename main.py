"""
主執行腳本
"""
import argparse
import subprocess
import os
import logging

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('main.log', mode='w')
    ]
)

def run_script(script_name, args=None):
    """執行指定的腳本"""
    command = ["uv", "run", "python", os.path.join("scripts", script_name)]
    if args:
        command.extend(args)

    try:
        logging.info(f"--- 正在執行腳本: {script_name} ---")
        subprocess.run(command, check=True)
        logging.info(f"--- 腳本 {script_name} 執行完畢 ---")
    except subprocess.CalledProcessError as e:
        logging.error(f"腳本 {script_name} 執行失敗: {e}")
    except FileNotFoundError:
        logging.error(f"找不到腳本: {script_name}，請確認檔案路徑。")

def main():
    """主函式"""
"""
主執行腳本
"""
import argparse
import subprocess
import os
import logging

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('main.log', mode='w')
    ]
)

def run_script(script_name, args=None):
    """執行指定的腳本"""
    command = ["uv", "run", "python", os.path.join("scripts", script_name)]
    if args:
        command.extend(args)

    try:
        logging.info(f"--- 正在執行腳本: {script_name} ---")
        subprocess.run(command, check=True)
        logging.info(f"--- 腳本 {script_name} 執行完畢 ---")
    except subprocess.CalledProcessError as e:
        logging.error(f"腳本 {script_name} 執行失敗: {e}")
    except FileNotFoundError:
        logging.error(f"找不到腳本: {script_name}，請確認檔案路徑。")

def main():
    """主函式"""
    parser = argparse.ArgumentParser(description="量化交易研究專案主執行器")
    parser.add_argument(
        "action",
        nargs='?', # Make action optional
        choices=['fetch', 'clean'],
        help="要執行的操作：'fetch' (獲取數據), 'clean' (清洗數據)"
    )
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4, 5], help='指定執行的階段 (1: Fetch, 2: Clean, 3: Margin, 4: Forex, 5: Z-Score)')
    parser.add_argument("--start", type=str, help="數據獲取開始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="數據獲取結束日期 (YYYY-MM-DD)")
    parser.add_argument('--full', action='store_true', help='執行所有階段')

    args = parser.parse_args()

    if args.full:
        logging.info("執行所有階段 (Full Run)...")
        run_script("01_fetch_data.py", ["--start", "2023-01-01", "--end", "2023-12-31"]) # Example dates
        run_script("02_clean_merge.py")
        run_script("03_strategy_margin.py")
        run_script("04_strategy_forex.py")
        run_script("05_strategy_futures_zscore.py")
    elif args.phase:
        if args.phase == 1:
            if not args.start or not args.end:
                logging.error("錯誤：執行階段 1 (Fetch) 需要 --start 和 --end 參數。")
                return
            run_script("01_fetch_data.py", ["--start", args.start, "--end", args.end])
        elif args.phase == 2:
            run_script("02_clean_merge.py")
        elif args.phase == 3:
            run_script("03_strategy_margin.py")
        elif args.phase == 4:
            run_script("04_strategy_forex.py")
        elif args.phase == 5:
            run_script("05_strategy_futures_zscore.py")
    elif args.action == 'fetch':
        if not args.start or not args.end:
            logging.error("錯誤：執行 'fetch' 操作需要 --start 和 --end 參數。")
            return
        run_script("01_fetch_data.py", ["--start", args.start, "--end", args.end])
    elif args.action == 'clean':
        run_script("02_clean_merge.py")
    else:
        logging.warning("請指定一個操作 ('fetch', 'clean'), 階段 (--phase), 或使用 --full 參數。")


if __name__ == "__main__":
    main()
