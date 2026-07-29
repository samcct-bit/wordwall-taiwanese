import re; html=open("wordwall_debug.html", encoding="utf-8").read(); print(len(re.findall(r"id=\"gameover_leaderboard\"", html)))
