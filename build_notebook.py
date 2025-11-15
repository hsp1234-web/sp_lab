import nbformat
from nbformat.v4 import new_notebook, new_code_cell

def create_notebook():
    """以程式化的方式建立一個新的、結構優化過的 Jupyter Notebook。"""

    # --- 儲存格 1: 設定並同步專案程式碼 ---
    # 更新重點：
    # - GIT_BRANCH 的預設值改為 "2.8"。
    cell1_code = """\
#@title 1. 設定並同步專案程式碼
# --- 解說 ---
# 這個儲存格會完成兩項核心任務：
# 1. 設定 GitHub 專案的 URL 和分支名稱 (可在此處修改)。
# 2. 根據設定，自動從 GitHub 下載或更新最新的程式碼。
import os
from IPython import get_ipython

# --- 參數設定 ---
GITHUB_REPO_URL = "https://github.com/hsp1234-web/sp_lab.git" #@param {type:"string"}
GIT_BRANCH = "6.1" #@param {type:"string"}

print("✅ 參數設定完成！")
print(f"   - 儲存庫: {GITHUB_REPO_URL}")
print(f"   - 分支: {GIT_BRANCH}")

# --- 程式碼同步 ---
repo_name = GITHUB_REPO_URL.split('/')[-1].replace('.git', '')
local_repo_path = os.path.join('/content', repo_name)
os.environ['LOCAL_REPO_PATH'] = local_repo_path

ipython = get_ipython()

if os.path.exists(local_repo_path):
    print(f"\\n🌀 專案資料夾已存在，正在更新至 '{GIT_BRANCH}' 分支...")
    ipython.run_line_magic('cd', local_repo_path)
    ipython.run_line_magic('system', 'git fetch -q origin && git checkout -q {GIT_BRANCH} && git pull -q origin {GIT_BRANCH}')
    ipython.run_line_magic('cd', '/content')
else:
    print(f"\\n✨ 專案資料夾不存在，正在從 '{GIT_BRANCH}' 分支下載...")
    ipython.run_line_magic('system', f'git clone -q --branch {GIT_BRANCH} {GITHUB_REPO_URL}')

print(f"✅ 程式碼同步完成！專案路徑: {local_repo_path}")
"""
    cell1 = new_code_cell(cell1_code, metadata={"title": "1. 設定並同步專案程式碼", "colab": {"code_folded": True}})

    # --- 儲存格 2: 安裝 Python 相依套件 ---
    # (此儲存格無需修改)
    cell2_code = """\
#@title 2. 安裝 Python 相依套件
# --- 解說 ---
# 這個儲存格會使用 uv (一個高速的 Python 套件安裝工具) 來安裝 `requirements.txt` 中定義的所有套件。
#
# 備註：uv 會自動偵測已安裝的套件，只下載與安裝缺失或版本不符的部分。
# 因此，重複執行此儲存格是安全的，且不會浪費時間在重複安裝上。
import os, sys
from IPython import get_ipython

local_repo_path = os.environ['LOCAL_REPO_PATH']
requirements_path = os.path.join(local_repo_path, 'requirements.txt')

ipython = get_ipython()

if not os.path.exists(requirements_path):
    print(f"⚠️ 警告：在專案路徑中找不到 requirements.txt 檔案。")
else:
    print("📦 正在強制重新安裝相依套件 (以解決 Colab 環境衝突)...")
    ipython.run_line_magic('system', 'pip install -q uv && uv pip install -q --reinstall -r {requirements_path}')
    print("✅ 所有套件安裝完畢！")

"""
    cell2 = new_code_cell(cell2_code, metadata={"title": "2. 安裝 Python 相依套件", "colab": {"code_folded": True}})

    # --- 儲存格 3: 【一鍵執行】啟動主流程 ---
    # 更新重點：
    # - 移除手動設定 sys.path 的程式碼。
    # - 將執行目標從 'src/main.py' 改為根目錄下的 'run.py'。
    # - 更新相關路徑與說明文字。
    cell3_code = """\
#@title 3. 【一鍵執行】啟動主流程
# --- 解說 ---
# 這是專案的核心執行儲存格。
# 它會從專案的根目錄，呼叫我們設計的 `run.py` 腳本來啟動整個流程。
# `run.py` 會自動處理 Python 模組的路徑問題，並執行包含回測、視覺化的完整流程。
# 最終的權益曲線圖將會直接顯示在此儲存格的輸出中。
import os
from IPython import get_ipython
from IPython.display import Image, display

local_repo_path = os.environ['LOCAL_REPO_PATH']
run_script_path = os.path.join(local_repo_path, 'run.py')
equity_curve_path = os.path.join(local_repo_path, 'src', 'output', 'sp_equity_curve.jpg')

ipython = get_ipython()

if not os.path.exists(run_script_path):
    print(f"❌ 錯誤：找不到主執行檔 {run_script_path}")
else:
    # 執行 run.py 前，需確保當前目錄位於專案根目錄
    ipython.run_line_magic('cd', local_repo_path)

    # 使用 %run 來執行，這能確保腳本在當前的 IPython kernel 中執行
    ipython.run_line_magic('run', 'run.py')

    # 顯示最終產出的圖表
    if os.path.exists(equity_curve_path):
        print("\\n--- 最終權益曲線圖 ---")
        display(Image(filename=equity_curve_path))
    else:
        print(f"⚠️ 警告：找不到預期的權益曲線圖檔案：{equity_curve_path}")

"""
    cell3 = new_code_cell(cell3_code, metadata={"title": "3. 【一鍵執行】啟動主流程", "colab": {"code_folded": True}})


    # --- 建立 Notebook ---
    nb = new_notebook(cells=[cell1, cell2, cell3],
                      metadata={
                          "colab": {"provenance": []},
                          "kernelspec": {
                              "display_name": "Python 3",
                              "name": "python3"
                          },
                          "language_info": {
                              "name": "python"
                          }
                      })

    return nb

if __name__ == "__main__":
    notebook = create_notebook()
    with open('sp_lab.ipynb', 'w') as f:
        nbformat.write(notebook, f)
    print("✅ `sp_lab.ipynb` 檔案已成功建立/更新。")
