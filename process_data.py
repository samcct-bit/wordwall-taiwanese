import csv
import json
import re

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
    return "其他主題單元"

def parse_unit(text):
    match = re.search(r'L(\d+)|第([一二三四五六七八九十])課', text)
    if match:
        if match.group(1):
            num = match.group(1)
            mapping = {'1':'一', '2':'二', '3':'三', '4':'四', '5':'五', '6':'六'}
            return f"第{mapping.get(num, num)}單元"
        elif match.group(2):
            return f"第{match.group(2)}單元"
    return "綜合單元"

def main():
    data = []
    with open('deep_wordwall_games.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row['Path']
            title = row['GameTitle']
            url = row['URL']
            
            combined_text = f"{path} {title}"
            
            # 使用原始抓取到的網址 (避免 404)
            play_url = url
            
            data.append({
                "category": parse_category(combined_text),
                "grade": parse_grade(combined_text),
                "term": parse_term(combined_text),
                "unit": parse_unit(combined_text),
                "title": title,
                "path": path,
                "wordwallUrl": play_url,
                "pptEmbedUrl": "" # 預留給 Google Slides 的欄位
            })

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"成功將 {len(data)} 筆遊戲轉換為 data.json！")

if __name__ == "__main__":
    main()
