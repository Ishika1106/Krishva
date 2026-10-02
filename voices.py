import pyttsx3

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    if not voices:
        print("No voices found. Please check your voice settings.")
    else:
        print(f" Found {len(voices)} voices:\n")
        for i, voice in enumerate(voices):
            print(f"{i}: {voice.name} - {voice.id}")
except Exception as e:
    print("Error initializing pyttsx3 or listing voices:")
    print(e)
