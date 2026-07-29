import argparse
import os
import shutil
import asyncio
import csv
import json
import re
import time
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

# ==========================================
# 1. INIT 命令：初始化模板
# ==========================================
def cmd_init(args):
    target_dir = args.dir
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"📁 建立資料夾：{target_dir}")
    
    template_dir = os.path.join(os.path.dirname(__file__), 'template')
    if not os.path.exists(template_dir):
        print(f"❌ 錯誤：找不到模板資料夾 {template_dir}")
        return
        
    for filename in ['index.html', 'styles.css', 'app.js']:
        src = os.path.join(template_dir, filename)
        dst = os.path.join(target_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ 已複製：{filename} -> {dst}")
        else:
            print(f"⚠️ 警告：模板檔案 {src} 不存在")
            
    print(f"\n🎉 專案初始化完成！請在 {target_dir} 中進行開發。")

# ==========================================
# 2. SCRAPE 命令：爬取 Wordwall 遊戲
# ==========================================
async def scroll_to_bottom(page):
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
    print(f"📂 目前位置：{current_path} (正在載入全部內容...)")
    await scroll_to_bottom(page)
    
    links = await page.evaluate('''() => {
        const anchors = Array.from(document.querySelectorAll('a'));
        return anchors.map(a => ({
            text: a.innerText.trim(),
            href: a.href,
            className: a.className
        })).filter(link => link.text !== '' && link.href !== '');
    }''')
    
    subfolders = []
    
    for link in links:
        href = link['href']
        className = link.get('className', '')
        title = link['text'].split('\n')[0].strip()
        
        if 'js-activity-item' in className and title:
            if not any(g['URL'] == href for g in all_games):
                all_games.append({
                    'Path': current_path,
                    'GameTitle': title,
                    'URL': href
                })
        elif 'js-folder-item' in className:
            try:
                folder_id = href.split('/folder/')[1].split('/')[0]
                if folder_id and folder_id not in visited_folders and not any(f['id'] == folder_id for f in subfolders):
                    subfolders.append({
                        'id': folder_id,
                        'title': title,
                        'href': href
                    })
            except IndexError:
                pass

    print(f"✅ 在 {current_path} 找到 {len([g for g in all_games if g['Path'] == current_path])} 個遊戲，以及 {len(subfolders)} 個未訪問過的子資料夾。")

    for folder in subfolders:
        print(f"\n👉 準備進入子資料夾: {folder['title']}")
        target_locator = page.locator(f"a[href*='/folder/{folder['id']}/']")
        
        if await target_locator.count() > 0:
            visited_folders.add(folder['id'])
            await target_locator.first.click()
            await asyncio.sleep(4)
            
            new_path = f"{current_path} > {folder['title']}"
            await scrape_current_view(page, new_path, all_games, visited_folders)
            
            print(f"🔙 從 {folder['title']} 返回 {current_path}")
            await page.evaluate('''() => {
                const crumbs = document.querySelectorAll('.js-breadcrumb');
                if (crumbs.length > 1) {
                    crumbs[crumbs.length - 2].click();
                } else if (crumbs.length === 1) {
                    crumbs[0].click();
                }
            }''')
            await asyncio.sleep(4)
            await scroll_to_bottom(page)
        else:
            print(f"⚠️ 找不到子資料夾 {folder['title']} 的點擊點。")

async def async_scrape(output_file):
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
        visited_folders = set()
        await asyncio.sleep(3)
        
        await scrape_current_view(page, "首頁", all_games, visited_folders)
        
        with open(output_file, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(["Path", "GameTitle", "URL"])
            for game in all_games:
                writer.writerow([game['Path'], game['GameTitle'], game['URL']])
                
        print(f"\n🎉 深度抓取任務完成！總共抓取到 {len(all_games)} 個遊戲連結！")
        print(f"資料已儲存至：{output_file}")
        
        await browser.close()

def cmd_scrape(args):
    asyncio.run(async_scrape(args.output))


# ==========================================
# 3. BUILD 命令：處理與編譯資料庫
# ==========================================
def parse_grade(text):
    if re.search(r'G1|一[上下]|一年級', text): return "一年級"
    if re.search(r'G2|二[上下]|二年級', text): return "二年級"
    if re.search(r'G3|三[上下]|三年級', text): return "三年級"
    if re.search(r'G4|四[上下]|四年級', text): return "四年級"
    if re.search(r'G5|五[上下]|五年級', text): return "五年級"
    if re.search(r'G6|六[上下]|六年級', text): return "六年級"
    return "不分年級"

def parse_term(text):
    if re.search(r'上學期|[一二三四五六]上|上冊', text): return "上學期"
    if re.search(r'下學期|[一二三四五六]下|下冊', text): return "下學期"
    return "不分學期"

def parse_category(text):
    if re.search(r'聲母|韻母|拼音|台羅|音標', text): return "音標遊戲"
    if re.search(r'俗語|諺語', text): return "俗語遊戲"
    # General parsing fallback
    if re.search(r'單字|生字', text): return "單字練習"
    if re.search(r'句型|造句', text): return "句型練習"
    return "其他主題單元"

def parse_unit(text):
    match = re.search(r'L(\d+)|第([一二三四五六七八九十])課|單元(\d+)', text)
    if match:
        if match.group(1):
            num = match.group(1)
            mapping = {'1':'一', '2':'二', '3':'三', '4':'四', '5':'五', '6':'六'}
            return f"第{mapping.get(num, num)}單元"
        elif match.group(2):
            return f"第{match.group(2)}單元"
        elif match.group(3):
            num = match.group(3)
            mapping = {'1':'一', '2':'二', '3':'三', '4':'四', '5':'五', '6':'六'}
            return f"第{mapping.get(num, num)}單元"
    return "綜合單元"

def cmd_build(args):
    data = []
    if not os.path.exists(args.input):
        print(f"❌ 錯誤：找不到輸入檔案 {args.input}")
        return
        
    with open(args.input, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row.get('Path', '')
            title = row.get('GameTitle', '')
            url = row.get('URL', '')
            
            combined_text = f"{path} {title}"
            
            data.append({
                "category": parse_category(combined_text),
                "grade": parse_grade(combined_text),
                "term": parse_term(combined_text),
                "unit": parse_unit(combined_text),
                "title": title,
                "path": path,
                "wordwallUrl": url,
                "pptEmbedUrl": ""
            })

    output_json = "data.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    # Write to target directory as data.js
    if args.dir:
        js_path = os.path.join(args.dir, 'data.js')
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write("window.gamesData = " + json.dumps(data, ensure_ascii=False, indent=4) + ";\n")
        print(f"✅ 成功將 {len(data)} 筆資料編譯為 {js_path}")
    else:
        print(f"✅ 成功將 {len(data)} 筆資料編譯為 {output_json}")

# ==========================================
# 4. ASSIGN 命令：自動派發作業
# ==========================================
def wait_for_user(msg="找不到按鈕。請在瀏覽器上手動點擊完成後，在此按下 Enter 鍵繼續..."):
    print(f"⚠️ {msg}")
    input("👉 處理完畢後，請在這裡按下 Enter 鍵繼續：")

def cmd_assign(args):
    input_file = args.input
    if not os.path.exists(input_file):
        print(f"❌ 找不到輸入檔案 {input_file}")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        games = json.load(f)
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 800}, locale='zh-TW')
        page = context.new_page()
        
        print("==================================================")
        print("【請手動登入 Wordwall】")
        print("登入網址已為您開啟。請點擊右上角的「登入」。")
        print("==================================================")
        page.goto("https://wordwall.net/tc")
        input("★ 登入完畢且看到「我的活動」或首頁後，請在這裡按下 Enter 鍵開始自動派發...")
        
        for idx, game in enumerate(games):
            print(f"\n[{idx+1}/{len(games)}] 正在處理遊戲：{game.get('title', 'Unknown')}")
            original_url = game.get('wordwallUrl', '')
            if not original_url:
                print("❌ 找不到原始網址，跳過。")
                continue
                
            game_id = original_url.rstrip('/').split('/')[-1]
            success_goto = False
            
            for try_url in [f"https://wordwall.net/tc/resource/private/{game_id}", f"https://wordwall.net/tc/edit/{game_id}", original_url]:
                print(f"👉 嘗試前往: {try_url}")
                try:
                    page.goto(try_url)
                    page.wait_for_load_state('networkidle')
                    if "myactivities" not in page.url:
                        success_goto = True
                        break
                except Exception:
                    continue
                    
            if not success_goto:
                wait_for_user(f"無法自動進入遊戲頁面。請搜尋此遊戲 ID「{game_id}」，點擊進入後再按 Enter。")
            
            time.sleep(1.5)
            try:
                print("🔍 尋找並點擊「課業分配」...")
                assign_btn = page.locator("text=課業分配 >> visible=true").first
                if assign_btn.count() == 0:
                    assign_btn = page.locator("text=設定作業 >> visible=true").first
                
                if assign_btn.count() > 0:
                    assign_btn.click(timeout=5000)
                else:
                    wait_for_user("找不到『課業分配』按鈕。")
                
                print("⚙️ 配置作業選項 (勾選排行榜、取消顯示答案)...")
                page.wait_for_load_state('networkidle')
                time.sleep(1.5)
                
                try:
                    page.locator('.js-gameover-leaderboard').last.check(force=True)
                except:
                    pass
                try:
                    page.locator('.js-gameover-review').last.uncheck(force=True)
                except:
                    pass
                    
                print("🔍 尋找並點擊「開始」...")
                start_btn = page.locator("text=/開始/ >> visible=true").last
                if start_btn.count() > 0:
                    start_btn.click(timeout=5000)
                else:
                    wait_for_user("找不到『開始』按鈕。")
                
                print("⏳ 等待專屬作業網址產生...")
                new_url = ""
                for _ in range(30):
                    inputs = page.locator('input[type="text"]').all()
                    for inp in inputs:
                        try:
                            val = inp.input_value()
                            if 'wordwall.net/play/' in val:
                                new_url = val
                                break
                        except:
                            pass
                    if new_url: break
                    time.sleep(0.5)
                
                if not new_url:
                    manual_url = input("👉 找不到網址。請手動複製作業網址「貼上」並按 Enter：").strip()
                    if 'wordwall.net/play/' in manual_url:
                        new_url = manual_url

                if new_url:
                    print(f"🎉 成功取得作業網址: {new_url}")
                    game['assignmentUrl'] = new_url
                    game['wordwallUrl'] = new_url
                else:
                    print("❌ 此題未能取得網址，保留原狀。")
                
                done_btn = page.locator("text=/完成/ >> visible=true").last
                if done_btn.count() > 0:
                    done_btn.click()
                    
            except Exception as e:
                print(f"❌ 發生錯誤: {e}")
                manual_url = input("👉 如果已手動完成派發，請貼上作業網址 (或按 Enter 跳過)：").strip()
                if 'wordwall.net/play/' in manual_url:
                    game['assignmentUrl'] = manual_url
                    game['wordwallUrl'] = manual_url
                    print(f"🎉 成功記錄網址: {manual_url}")
                
        output_file = args.output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=4)
        
        # If deploying to a specific dir, also save to data.js
        if args.dir:
            js_path = os.path.join(args.dir, 'data.js')
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write("window.gamesData = " + json.dumps(games, ensure_ascii=False, indent=4) + ";\n")
            print(f"✅ 已同步更新 {js_path}")
            
        print("\n==================================================")
        print("✅ 全面派發完成！")
        print(f"資料已儲存為 {output_file}")
        print("==================================================")
        browser.close()

# ==========================================
# Main CLI Parser
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Wordwall CLI - 管理、抓取與建立靜態檢索網站工具")
    subparsers = parser.add_subparsers(dest="command", help="可用指令")
    subparsers.required = True

    # 1. init
    parser_init = subparsers.add_parser("init", help="初始化一個全新的 Wordwall 檢索網站資料夾")
    parser_init.add_argument("dir", type=str, help="目標資料夾名稱 (例如: my-wordwall-site)")

    # 2. scrape
    parser_scrape = subparsers.add_parser("scrape", help="從 Wordwall 抓取所有遊戲")
    parser_scrape.add_argument("--output", type=str, default="deep_wordwall_games.csv", help="輸出的 CSV 檔案名稱")

    # 3. build
    parser_build = subparsers.add_parser("build", help="編譯原始 CSV 資料並發布至網頁專案中")
    parser_build.add_argument("--input", type=str, default="deep_wordwall_games.csv", help="輸入的 CSV 檔案名稱")
    parser_build.add_argument("--dir", type=str, help="(選填) 將 data.js 直接輸出到指定的網頁資料夾中", default=".")

    # 4. assign
    parser_assign = subparsers.add_parser("assign", help="自動為資料庫中的遊戲派發學生作業連結")
    parser_assign.add_argument("--input", type=str, default="data.json", help="輸入的 JSON 檔案名稱")
    parser_assign.add_argument("--output", type=str, default="data_with_assignments.json", help="輸出的 JSON 檔案名稱")
    parser_assign.add_argument("--dir", type=str, help="(選填) 同步將更新後的 data.js 輸出到指定的網頁資料夾中", default=".")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "assign":
        cmd_assign(args)

if __name__ == "__main__":
    main()
