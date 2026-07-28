import asyncio
from playwright.async_api import async_playwright
import csv
import os

async def main():
    # 讀取剛剛抓取的資料夾清單
    folders = []
    if os.path.exists('wordwall_links.csv'):
        with open('wordwall_links.csv', mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('URL', '')
                if '/myactivities/folder/' in url:
                    # 取出資料夾名稱 (第一行)
                    title = row.get('Title', '').split('\n')[0].strip()
                    folders.append({'title': title, 'url': url})

    print(f"找到 {len(folders)} 個資料夾，準備進入抓取裡面的遊戲！")
    
    if not folders:
        print("沒有找到資料夾，程式結束。")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n前往 Wordwall 網站...")
        await page.goto("https://wordwall.net/myactivities")
        
        print("\n" + "="*50)
        print("【請在瀏覽器中手動登入您的帳號】")
        print("為了能進入資料夾抓取，請您再次登入。")
        print("="*50 + "\n")
        
        input("★ 登入完畢且看到「我的活動」畫面後，請在這裡按下 Enter 鍵...")
        
        all_games = []
        
        # 依序進入每個資料夾抓取
        # 注意：我們現在已經在「我的活動」首頁了
        for i, folder in enumerate(folders):
            print(f"\n正在進入資料夾 ({i+1}/{len(folders)}): {folder['title']} ...")
            try:
                # 1. 透過資料夾 ID 來精確模擬點擊
                folder_url = folder['url']
                try:
                    folder_id = folder_url.split('/folder/')[1].split('/')[0]
                except IndexError:
                    folder_id = ""
                
                if folder_id:
                    target_locator = page.locator(f"a[href*='/folder/{folder_id}/']")
                    if await target_locator.count() > 0:
                        # 點擊資料夾
                        await target_locator.first.click()
                    else:
                        print(f"⚠️ 在畫面上找不到資料夾 {folder['title']} 的連結 (ID:{folder_id})，跳過此資料夾。")
                        continue
                else:
                    print(f"⚠️ 無法解析資料夾網址: {folder_url}")
                    continue
                
                # 2. 等待資料夾內容載入
                await asyncio.sleep(5)
                
                # 3. 自動向下捲動直到沒有新內容，確保所有遊戲都被載入
                scroll_attempts = 0
                last_count = await page.evaluate("document.querySelectorAll('a').length")
                while scroll_attempts < 15:
                    await page.evaluate('''() => {
                        const items = document.querySelectorAll('.js-item');
                        if (items.length > 0) {
                            items[items.length - 1].scrollIntoView(true);
                        }
                    }''')
                    await asyncio.sleep(2)
                    
                    new_count = await page.evaluate("document.querySelectorAll('a').length")
                    if new_count == last_count:
                        break
                    last_count = new_count
                    scroll_attempts += 1
                
                # 4. 抓取資料夾內的遊戲
                links = await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll('a'));
                    return anchors.map(a => ({
                        text: a.innerText.trim(),
                        href: a.href,
                        className: a.className
                    })).filter(link => link.text !== '' && link.href !== '');
                }''')
                
                game_count = 0
                for link in links:
                    if '/resource/' in link['href'] or '/play/' in link['href']:
                        game_title = link['text'].split('\n')[0].strip()
                        if game_title and "⋮" not in game_title:
                            all_games.append({
                                'Folder': folder['title'],
                                'GameTitle': game_title,
                                'URL': link['href']
                            })
                            game_count += 1
                        
                print(f"✅ 在此資料夾找到 {game_count} 個遊戲。")
                
                # 5. 返回上一頁 (我的活動首頁)
                await page.go_back()
                await asyncio.sleep(3) # 等待首頁重新載入
                
            except Exception as e:
                print(f"❌ 讀取資料夾 {folder['title']} 時發生錯誤: {e}")
                # 如果發生錯誤，嘗試強行回到首頁以拯救後續的資料夾
                try:
                    await page.goto("https://wordwall.net/tc/myactivities")
                    await asyncio.sleep(4)
                except:
                    pass

        # 寫出所有遊戲
        output_csv = "all_wordwall_games.csv"
        with open(output_csv, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(["Folder", "GameTitle", "URL"])
            for game in all_games:
                writer.writerow([game['Folder'], game['GameTitle'], game['URL']])
                
        print(f"\n🎉 任務完成！共抓取到 {len(all_games)} 個遊戲連結！")
        print(f"資料已儲存至：{output_csv}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
