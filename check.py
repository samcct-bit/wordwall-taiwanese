import re; html=open("wordwall_debug.html", encoding="utf-8").read(); print([m.group(0) for m in re.finditer(r"<input[^>]*>", html, re.IGNORECASE) if "text" in m.group(0)])
