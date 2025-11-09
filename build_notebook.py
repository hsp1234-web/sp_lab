import nbformat
from nbformat.v4 import new_notebook, new_code_cell

def create_notebook():
    """以程式化的方式建立一個新的 Jupyter Notebook。"""

    # --- 儲存格 1: 設定 GitHub 儲存庫與分支 ---
    cell1_code = """\
#@title 1. 設定 GitHub 儲存庫與分支
# --- 解說 ---
# 這個儲存格負責設定要下載的 GitHub 專案 URL 和分支名稱。
# 您可以在這裡修改 GITHUB_REPO_URL 和 GIT_BRANCH 的值，以指向您自己的儲存庫或分支。
import os

GITHUB_REPO_URL = "https://github.com/hsp1234-web/sp_lab.git" #@param {type:"string"}
GIT_BRANCH = "2.1" #@param {type:"string"}

os.environ['GITHUB_REPO_URL'] = GITHUB_REPO_URL
os.environ['GIT_BRANCH'] = GIT_BRANCH

print("✅ 參數設定完成！")
print(f"   - 儲存庫: {GITHUB_REPO_URL}")
print(f"   - 分支: {GIT_BRANCH}")
"""
    cell1 = new_code_cell(cell1_code, metadata={"title": "1. 設定 GitHub 儲存庫與分支"})

    # --- 儲存格 2: 下載或更新專案程式碼 ---
    cell2_code = """\
#@title 2. 下載或更新專案程式碼
# --- 解說 ---
# 這個儲存格會從您指定的 GitHub 分支下載或更新專案程式碼。
# 如果專案資料夾已存在，它會執行 `git pull` 來獲取最新版本。
# 如果不存在，它會執行 `git clone` 來完整下載。
import os
from IPython import get_ipython

GITHUB_REPO_URL = os.environ['GITHUB_REPO_URL']
GIT_BRANCH = os.environ['GIT_BRANCH']
repo_name = GITHUB_REPO_URL.split('/')[-1].replace('.git', '')
local_repo_path = os.path.join('/content', repo_name)
os.environ['LOCAL_REPO_PATH'] = local_repo_path

ipython = get_ipython()

if os.path.exists(local_repo_path):
    print(f"🌀 專案資料夾已存在，正在更新至 '{GIT_BRANCH}' 分支...")
    ipython.run_line_magic('cd', local_repo_path)
    ipython.run_line_magic('system', 'git fetch -q origin && git checkout -q {GIT_BRANCH} && git pull -q origin {GIT_BRANCH}')
    ipython.run_line_magic('cd', '/content')
else:
    print(f"✨ 專案資料夾不存在，正在從 '{GIT_BRANCH}' 分支下載...")
    ipython.run_line_magic('system', f'git clone -q --branch {GIT_BRANCH} {GITHUB_REPO_URL}')

print(f"✅ 程式碼同步完成！專案路徑: {local_repo_path}")
"""
    cell2 = new_code_cell(cell2_code, metadata={"title": "2. 下載或更新專案程式碼"})

    # --- 儲存格 3: 安裝 Python 相依套件 ---
    cell3_code = """\
#@title 3. 安裝 Python 相依套件
# --- 解說 ---
# 這個儲存格會使用 uv (一個高速的 Python 套件安裝工具)
# 來安裝 `requirements.txt` 中定義的所有 Python 套件。
# 同時，它會將專案資料夾加入到 Python 的執行路徑中，以確保能正確匯入專案模組。
import os, sys
from IPython import get_ipython

local_repo_path = os.environ['LOCAL_REPO_PATH']
requirements_path = os.path.join(local_repo_path, 'requirements.txt')

ipython = get_ipython()

if not os.path.exists(requirements_path):
    print(f"⚠️ 警告：在專案路徑中找不到 requirements.txt 檔案。")
else:
    print("📦 正在安裝相依套件...")
    ipython.run_line_magic('system', 'pip install -q uv && uv pip install -q -r {requirements_path}')
    print("✅ 所有套件安裝完畢！")

# 將專案路徑加入 sys.path
if local_repo_path not in sys.path:
    sys.path.insert(0, local_repo_path)
    print(f"🐍 已將專案路徑加入 Python 執行環境。")
"""
    cell3 = new_code_cell(cell3_code, metadata={"title": "3. 安裝 Python 相依套件"})

    # --- 儲存格 4: 【一鍵執行】啟動主流程 ---
    cell4_code = """\
#@title 4. 【一鍵執行】啟動主流程
# --- 解說 ---
# 這是專案的核心執行儲存格。
# 它會進入 `src` 目錄，並呼叫 `main.py` 腳本來完整執行整個量化研究流程，
# 包含數據獲取、清洗、特徵建立、訊號生成、回測、成本分析與視覺化。
# 最終的權益曲線圖將會直接顯示在此儲存格的輸出中。
import os
from IPython import get_ipython
from IPython.display import Image, display

local_repo_path = os.environ['LOCAL_REPO_PATH']
src_path = os.path.join(local_repo_path, 'src')
output_path = os.path.join(src_path, 'output')
main_script_path = os.path.join(src_path, 'main.py')
equity_curve_path = os.path.join(output_path, 'equity_curve.jpg')

ipython = get_ipython()

if not os.path.exists(main_script_path):
    print(f"❌ 錯誤：找不到主執行檔 {main_script_path}")
else:
    print("🚀 即將啟動全自動化回測流程...")
    ipython.run_line_magic('cd', src_path)
    ipython.run_line_magic('run', 'main.py')
    print("✅ 主流程執行完畢！")

    # 顯示最終產出的圖表
    if os.path.exists(equity_curve_path):
        print("\\n--- 最終權益曲線圖 ---")
        display(Image(filename=equity_curve_path))
    else:
        print(f"⚠️ 警告：找不到預期的權益曲線圖檔案：{equity_curve_path}")

"""
    cell4 = new_code_cell(cell4_code, metadata={"title": "4. 【一鍵執行】啟動主流程"})


    # --- 建立 Notebook ---
    nb = new_notebook(cells=[cell1, cell2, cell3, cell4],
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
    print("✅ `sp_lab.ipynb` 檔案已成功建立。")
