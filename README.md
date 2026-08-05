# Wordwall 整合檢索平台與 CLI 工具

這是一個強大的工具套件，可以幫助您將個人的 Wordwall 帳號中的遊戲，自動抓取、整理，並產生一個美觀、具備響應式設計 (RWD) 的靜態檢索網站。

## 特色
1. **一鍵爬蟲**：自動遍歷 Wordwall 資料夾，找出所有的遊戲連結。
2. **自動派發作業**：透過 Playwright 自動幫每一款遊戲建立「學生專屬作業連結（附排行榜）」。
3. **靜態網頁產生**：自動將抓取到的資料轉為 `data.js`，搭配內建的網站模板，打造能放在 GitHub Pages 的靜態網站。
4. **手機完美支援**：產生的網站具備響應式介面、左側橫向滑動選單與簡報抽屜。

## 安裝需求
本專案採用 Python 撰寫，需安裝 Playwright 作為瀏覽器自動化工具。
```bash
pip install playwright
playwright install chromium
```

## CLI 工具使用說明 (`ww.py`)

本專案提供了一支整合型的 CLI 工具 `ww.py`，支援以下五大功能：

### ⭐ 日常推薦指令：智慧增量同步 (`sync`)
當您在 Wordwall 新增了幾款遊戲，想要快速更新到現有網站時，請直接使用此指令。
```bash
python ww.py sync --dir my-website
```
> **這會自動完成所有事情**：先爬取最新遊戲、比對舊有資料庫、保留舊遊戲的作業連結，並**只針對新遊戲**自動登入派發作業。最後自動將更新後的 `data.js` 匯出至您的網站目錄。

### 1. 初始化網站模板 (`init`)
在指定的資料夾中，建立一個全新的網頁版型（包含 HTML、CSS、JS）。
```bash
python ww.py init my-website
```
> 將會在 `./my-website/` 目錄中產生 `index.html`, `styles.css` 與 `app.js`。

### 2. 爬取遊戲資料 (`scrape`)
自動登入 Wordwall 並爬取帳號內的所有遊戲與資料夾架構。
```bash
python ww.py scrape --output deep_wordwall_games.csv
```
> 執行後會開啟瀏覽器請您登入，登入後按下 Enter，腳本就會開始自動爬取，並輸出 CSV 檔。

### 3. 編譯資料庫 (`build`)
讀取上一步的 CSV 檔，根據自訂規則（如：G1 -> 一年級）將資料編譯為 JSON，並產生靜態網頁所需的 `data.js`。
```bash
python ww.py build --input deep_wordwall_games.csv --dir my-website
```
> 💡 **智慧保留連結**：`build` 指令現在具備智慧合併功能，重建 JSON 時會自動讀取舊 `data.json` 並保留已有的作業連結，不用擔心重新編譯會導致原有的派發紀錄遺失。

### 5. 自動派發作業 (`assign`)
(進階功能) 讀取 `data.json`，自動登入 Wordwall 幫每款遊戲點擊「課業分配」，並抓取專屬連結。
```bash
python ww.py assign --input data.json --output data_with_assignments.json --dir my-website
```
> 💡 **跳過已有作業**：腳本會自動檢查並「跳過」已經成功派發過作業的遊戲。因此配合 `sync` 指令或智慧 `build`，只會針對缺少連結的新遊戲進行自動化派發。

## 如何自訂分類標籤？
如果您需要調整 `build` 指令在辨識「年級」、「單元」等標籤的邏輯，您可以直接修改 `ww.py` 中的 `parse_grade()`, `parse_category()` 等函式，利用正則表達式打造符合您個人習慣的命名規則！
