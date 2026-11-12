import asyncio, json, edge_tts

async def main():
    words = []
    tts = edge_tts.Communicate(open("script.txt").read(), "en-US-AndrewNeural", rate="-4%", boundary="WordBoundary")
    async for chunk in tts.stream():
        if chunk["type"] == "WordBoundary":
            words.append({
                "w": chunk["text"],
                "start": round(chunk["offset"] / 1e7, 3),
                "end": round((chunk["offset"] + chunk["duration"]) / 1e7, 3),
            })
    json.dump(words, open("vo-words.json", "w"), indent=1)
    print(f"{len(words)} words, last ends at {words[-1]['end']}s")
    # print scene-boundary candidates (sentence ends)
    for i, w in enumerate(words):
        if w["w"].rstrip(".") in ("gone", "keywords", "graph", "demand.", "keywords.", "qualified."):
            print(f"  sentence end: {w['w']} @ {w['end']}s")

asyncio.run(main())
