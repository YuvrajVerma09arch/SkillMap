import re

def clean_data(data):
    if not data or not data.strip():
        return ""

    text = data.lower()
    bullets = r"[•▪●■–—]"
    text = re.sub(bullets, " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text
