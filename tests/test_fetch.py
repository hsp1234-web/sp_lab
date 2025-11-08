import os
import pytest
from src.fetch import download_gspc  # 預期從 src/fetch.py 導入函式

# 定義測試用的常數
TICKER = "^GSPC"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "GSPC.parquet")

@pytest.fixture(scope="module")
def setup_teardown():
    """測試前置與後置處理"""
    # 測試前：確保檔案不存在
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    yield  # 執行測試

    # 測試後：清理檔案
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

def test_download_gspc_creates_file(setup_teardown):
    """
    測試 download_gspc 函式是否成功下載資料並建立 Parquet 檔案。
    """
    # 1. 確認前提：檔案在執行前不存在
    assert not os.path.exists(OUTPUT_FILE), f"測試前置作業失敗，檔案 {OUTPUT_FILE} 已存在。"

    # 2. 執行目標函式
    download_gspc()

    # 3. 驗證結果：檔案在執行後已建立
    assert os.path.exists(OUTPUT_FILE), f"函式執行後，檔案 {OUTPUT_FILE} 未被建立。"
