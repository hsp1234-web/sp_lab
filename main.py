"""
主執行腳本
"""
import argparse
import subprocess
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
    command = ["uv", "run", "python", f"scripts/{script_name}"]
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
        choices=['fetch', 'clean'],
        help="要執行的操作：'fetch' (獲取數據), 'clean' (清洗數據)"
    )
    parser.add_argument("--start", type=str, help="數據獲取開始日期 (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="數據獲取結束日期 (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.action == 'fetch':
        if not args.start or not args.end:
            logging.error("錯誤：執行 'fetch' 操作需要 --start 和 --end 參數。")
            return
        run_script("01_fetch_data.py", ["--start", args.start, "--end", args.end])

    elif args.action == 'clean':
        run_script("02_clean_merge.py")

if __name__ == "__main__":
    main()
