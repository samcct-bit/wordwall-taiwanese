import asyncio
from playwright.async_api import async_playwright
import csv

async def scroll_to_bottom(page):
    """將目前的視圖捲動到最底部，確保動態載入的項目都出現"""
    scroll_attempts = 0
    last_count = await page.evaluate("document.querySelectorAll('.js-item').length")
    while scroll_attempts < 15:
        await page.evaluate('''() => {
            const items = document.querySelectorAll('.js-item');
            if (items.length > 0) {
                items[items.length - 1].scrollIntoView(true);
            }
        }''')
        await asyncio.sleep(2)
        new_count = await page.evaluate("document.querySelectorAll('.js-item').length")
        if new_count == last_count:
            break
        last_count = new_count
        scroll_attempts += 1

async def scrape_current_view(page, current_path, all_games, visited_folders):
    """
    抓取目前畫面中的所有遊戲，並尋找是否有子資料夾。
    如果有子資料夾，則遞迴點擊進入抓取。
    """
    print(f"📂 目前位置：{current_path} (正在載入全部內容...)")
    await scroll_to_bottom(page)
    
    # 取得畫面上所有的連結資訊
    links = await page.evaluate('''() => {
        const anchors = Array.from(document.querySelectorAll('a'));
        return anchors.map(a => ({
            text: a.innerText.trim(),
            href: a.href,
            className: a.className
        })).filter(link => link.text !== '' && link.href !== '');
    }''')
    
    subfolders = []
    
    # 分類連結：找出遊戲與子資料夾
    for link in links:
        href = link['href']
        className = link.get('className', '')
        title = link['text'].split('\n')[0].strip()
        
        # 如果是遊戲 (透過 class 判斷)
        if 'js-activity-item' in className and title:
            if not any(g['URL'] == href for g in all_games):
                all_games.append({
                    'Path': current_path,
                    'GameTitle': title,
                    'URL': href
                })
                
        # 如果是子資料夾 (透過 class 判斷)
        elif 'js-folder-item' in className:
            try:
                # 擷取資料夾 ID
                folder_id = href.split('/folder/')[1].split('/')[0]
                # 過濾掉已經訪問過的資料夾 (例如側邊欄會重複顯示所有資料夾)
                if folder_id and folder_id not in visited_folders and not any(f['id'] == folder_id for f in subfolders):
                    subfolders.append({
                        'id': folder_id,
                        'title': title,
                        'href': href
                    })
            except IndexError:
                pass

    print(f"✅ 在 {current_path} 找到 {len([g for g in all_games if g['Path'] == current_path])} 個遊戲，以及 {len(subfolders)} 個未訪問過的子資料夾。")

    # 依序進入每個子資料夾
    for folder in subfolders:
        print(f"\n👉 準備進入子資料夾: {folder['title']}")
        target_locator = page.locator(f"a[href*='/folder/{folder['id']}/']")
        
        if await target_locator.count() > 0:
            # 標記為已訪問
            visited_folders.add(folder['id'])
            await target_locator.first.click()
            await asyncio.sleep(4) # 等待資料夾載入
            
            # 遞迴抓取裡面的內容
            new_path = f"{current_path} > {folder['title']}"
            await scrape_current_view(page, new_path, all_games, visited_folders)
            
            # 抓取完畢後，返回上一層！
            print(f"🔙 從 {folder['title']} 返回 {current_path}")
            # 點擊上方的麵包屑 (Breadcrumb) 返回上一層資料夾
            await page.evaluate('''() => {
                const crumbs = document.querySelectorAll('.js-breadcrumb');
                if (crumbs.length > 1) {
                    crumbs[crumbs.length - 2].click();
                } else if (crumbs.length === 1) {
                    crumbs[0].click();
                }
            }''')
            await asyncio.sleep(4)
            # 返回上一層後，可能需要重新滾動才能把所有的資料夾顯示出來
            await scroll_to_bottom(page)
            
        else:
            print(f"⚠️ 找不到子資料夾 {folder['title']} 的點擊點。")


async def main():
    print("啟動深度抓取機器人 (支援無限層級子資料夾)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://wordwall.net/tc/myactivities")
        
        print("\n" + "="*50)
        print("【請手動登入 Wordwall】")
        print("="*50 + "\n")
        
        input("★ 登入完畢且看到「我的活動」畫面後，請在這裡按下 Enter 鍵...")
        
        all_games = []
        visited_folders = set()  # 用來記錄已經進去過的資料夾，避免迷路死迴圈
        await asyncio.sleep(3)
        
        # 從根目錄開始遞迴抓取
        await scrape_current_view(page, "首頁", all_games, visited_folders)
        
        # 寫出所有遊戲
        output_csv = "deep_wordwall_games.csv"
        with open(output_csv, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(["Path", "GameTitle", "URL"])
            for game in all_games:
                writer.writerow([game['Path'], game['GameTitle'], game['URL']])
                
        print(f"\n🎉 深度抓取任務完成！總共抓取到 {len(all_games)} 個遊戲連結！")
        print(f"資料已儲存至：{output_csv}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
