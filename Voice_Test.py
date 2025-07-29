from naoqi import ALProxy
import time

# Replace with Pepper's IP address
PEPPER_IP = "192.168.0.102"
PORT = 9559

# Emotion voice settings
emotion_settings = {
    "Happy":    {"vct": 150, "rspd": 100, "vol": 100, "pau": 100},
    "Sad":      {"vct": 80,  "rspd": 70,  "vol": 70,  "pau": 1000},
    "Disgust":  {"vct": 70,  "rspd": 90,  "vol": 100, "pau": 400},
    "Angry":    {"vct": 60,  "rspd": 110, "vol": 130, "pau": 100},
    "Surprise": {"vct": 130, "rspd": 120, "vol": 110, "pau": 300},
    "Fear":     {"vct": 90,  "rspd": 80,  "vol": 90,  "pau": 700},
    "Confused": {"vct": 100, "rspd": 90,  "vol": 90,  "pau": 500},
    "Neutral":  {"vct": 100, "rspd": 100, "vol": 100, "pau": 100}
}

# Sample sentence to say
sample_text = "I am currently expressing the emotion: {}."

def main():
    try:
        tts = ALProxy("ALTextToSpeech", PEPPER_IP, PORT)

        for emotion, settings in emotion_settings.items():
            vct = settings["vct"]
            rspd = settings["rspd"]
            vol = settings["vol"]
            pau = settings["pau"]

            # Construct QiChat with tags
            speech = (
                "\\vct={}\\"
                "\\rspd={}\\"
                "\\vol={}\\"
                "{}"
                "\\pau={}\\"
            ).format(vct, rspd, vol, sample_text.format(emotion), pau)

            print("Speaking with emotion: {emotion}")
            tts.say(speech)
            time.sleep(2)  # Wait before next emotion

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
