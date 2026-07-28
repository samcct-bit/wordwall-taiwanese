import asyncio
from playwright.async_api import async_playwright
import csv

async def main():
    print("正在啟動瀏覽器...")
    async with async_playwright() as p:
        # 使用 non-headless 模式，讓您可以操作瀏覽器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 前往 Wordwall 登入或我的活動頁面
        print("前往 Wordwall 網站...")
        await page.goto("https://wordwall.net/myactivities")

        print("\n" + "="*50)
        print("【請在彈出的瀏覽器視窗中進行操作】")
        print("1. 請手動登入您的 Wordwall 帳號。")
        print("2. 登入後，請確保您停留在「我的活動 (My Activities)」頁面。")
        print("3. 如果您有很多遊戲，請向下滾動讓所有遊戲載入完成。")
        print("="*50 + "\n")
        
        input("★ 請確認網頁『已經完全載入完畢』且『沒有在轉圈圈』後，再在「這裡」按下 Enter 鍵繼續執行爬蟲...")

        print("\n開始抓取頁面資料...")
        
        try:
            # 確保頁面狀態穩定，避免剛好遇到網頁跳轉
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            
            # 抓取頁面上所有的連結與文字
            links = await page.evaluate('''() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors.map(a => ({
                    text: a.innerText.trim(),
                    href: a.href,
                    className: a.className
                })).filter(link => link.text !== '' && link.href !== '');
            }''')

            # 將資料存入 CSV
            csv_filename = "wordwall_links.csv"
            with open(csv_filename, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["Title", "URL", "ClassName"])
                
                for link in links:
                    writer.writerow([link['text'], link['href'], link['className']])
                    
            print(f"\n✅ 抓取完成！共找到 {len(links)} 個連結。")
            print(f"資料已儲存至目前的資料夾：{csv_filename}")
            
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")
            print("這通常是因為在按下 Enter 的瞬間，網頁剛好在重新整理或跳轉頁面。請重新執行一次腳本。")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
