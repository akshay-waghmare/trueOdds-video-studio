import whisper, json

model = whisper.load_model("small.en")
result = model.transcribe("assets/vo-powerplay-signal.wav", word_timestamps=True)

words = []
for seg in result["segments"]:
    for w in seg.get("words", []):
        words.append({"word": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)})

with open("assets/vo-powerplay-signal.json", "w") as f:
    json.dump({"words": words}, f, indent=2)

print(f"Done: {len(words)} words")
for w in words:
    print(f"  {w['start']:5.2f}-{w['end']:5.2f}  {w['word']}")
