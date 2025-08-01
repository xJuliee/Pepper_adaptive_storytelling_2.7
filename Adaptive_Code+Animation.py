# -*- coding: utf-8 -*-
from naoqi import ALProxy
import socket
import time
import struct
import cv2
import numpy as np
import threading
import sys

# === Pepper Configuration ===
PEPPER_IP = "192.168.0.102"
PEPPER_PORT = 9559

# === Laptop Streaming Target ===
LAPTOP_IP = "10.9.73.57"
LAPTOP_PORT = 5000          # Laptop's image receiver port
PEPPER_RECEIVE_PORT= 6000  # Port to receive classified emotion back

# === Pepper Camera Setup ===
resolution = 2  # 640x480
color_space = 13  # kBGRColorSpace
fps = 10

camera_name = "pepperStream"
capture_id = None
sock = None

# === Initialize TTS and AnimatedSpeech services ===
try:
    tts = ALProxy("ALTextToSpeech", PEPPER_IP, PEPPER_PORT)
    tts.setLanguage("English")
except Exception as e:
    print("[TTS Init] Failed to connect to ALTextToSpeech:", e)
    tts = None

try:
    animated_speech = ALProxy("ALAnimatedSpeech", PEPPER_IP, PEPPER_PORT)
except Exception as e:
    print("[AnimatedSpeech Init] Failed to connect to ALAnimatedSpeech:", e)
    animated_speech = None

# === Emotion-based Speech Tagging ===
def get_speech_tags(emotion):
    settings = {
        "happy":     {"vct":150, "rspd":100, "vol":80, "pau":100},
        "sad":       {"vct":80,  "rspd":70,  "vol":65,  "pau":1000},
        "angry":     {"vct":60,  "rspd":100, "vol":100, "pau":100},
        "surprise":  {"vct":130, "rspd":100, "vol":88, "pau":300},
        "fear":      {"vct":90,  "rspd":80,  "vol":72,  "pau":700},
        "confused":  {"vct":100, "rspd":90,  "vol":72,  "pau":500},
        "neutral":   {"vct":100, "rspd":100, "vol":80, "pau":100},
        "disgust":   {"vct":70,  "rspd":90,  "vol":80, "pau":400}
    }
    return settings.get(emotion.lower(), {"vct":100, "rspd":100, "vol":80, "pau":100})

# === Emotion Receiving Function with Speech and Animation ===
def emotion_receiver():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PEPPER_RECEIVE_PORT))
    server_socket.listen(5)
    print("[Emotion Receiver] Listening on port", PEPPER_RECEIVE_PORT)

    # Map emotion to fixed speech phrases
    emotion_to_phrase = [
    {
        "neutral": "It was raining that morning.",
        "happy": "It was barely raining that morning.",
        "sad": "It was pouring rain that morning.",
        "angry": "Of course it rained—on that morning of all days.",
        "disgust": "Yet again, it was raining that morning.",
        "fear": "The rain hammered down that morning.",
        "surprise": "It had never rained like that before that morning.",
        "confused": "I’m not even sure if it rained that morning."
    },
    {
        "neutral": "I stood on the platform, clutching the umbrella.",
        "happy": "I stood on the platform, thankful for the umbrella.",
        "sad": "I stood on the platform, soaked and wishing I hadn’t forgotten the umbrella.",
        "angry": "I stood on the platform, fuming that I’d left the umbrella behind.",
        "disgust": "I stood on the platform, the sour rain seeping through despite the umbrella.",
        "fear": "I stood on the platform, panicked that I’d forgotten the umbrella.",
        "surprise": "I stood on the platform, stunned to find I’d brought the umbrella after all.",
        "confused": "I stood on the platform, trying to remember where I’d left the umbrella."
    },
    {
        "neutral": "The train was late.",
        "happy": "The train was late—a rare surprise.",
        "sad": "The train was late—once again.",
        "angry": "The train was late—as always.",
        "disgust": "The train was late—because of course it was.",
        "fear": "The train was late—far longer than usual.",
        "surprise": "The train was late—for the very first time.",
        "confused": "The train was late—though I hadn’t noticed at first."
    },
    {
        "neutral": "People huddled under the awning, quiet.",
        "happy": "People huddled under the awning, and somewhere, someone was softly singing.",
        "sad": "People huddled under the awning, quiet and resigned.",
        "angry": "People huddled under the awning, muttering complaints under their breath.",
        "disgust": "People huddled under the awning, packed in too close for comfort.",
        "fear": "People huddled under the awning, silent—like something was about to happen.",
        "surprise": "People huddled under the awning, quiet—until someone started to sing.",
        "confused": "People huddled under the awning, uncertain what was going on."
    },
    {
        "neutral": "I almost missed it—the man across from me, fumbling with an envelope, his hands shaking slightly.",
        "happy": "I almost missed it—the man across from me, fumbling with an envelope, his hands holding it gently.",
        "sad": "I almost missed it—the man across from me, fumbling with a soaked envelope, his hands barely steady.",
        "angry": "I almost missed it—the man across from me, fumbling with a drenched envelope, his hands clenched tight.",
        "disgust": "I almost missed it—the man across from me, fumbling with a soggy, dripping envelope, his hands twitching.",
        "fear": "I almost missed it—the man across from me, fumbling with a soaked envelope, his hands trembling hard.",
        "surprise": "I almost missed it—the man across from me, fumbling with an envelope, his hands twitching oddly.",
        "confused": "I almost missed it—the man across from me, fumbling with a wet envelope, his hands moving strangely."
    },
    {
        "neutral": "He looked nonchalant. Casual, even.",
        "happy": "He looked proud. Victorious, even.",
        "sad": "He looked drained. Defeated, even.",
        "angry": "He looked tense. Furious, even.",
        "disgust": "He looked uneasy. Disgusted, even.",
        "fear": "He looked startled. Frightened, even.",
        "surprise": "He looked amazed. Wondrous, even.",
        "confused": "He looked uncertain. Lost, even."
    },
    {
        "neutral": "As he dropped the letter, I bent down to pick it up.",
        "happy": "As he dropped the letter, I bent down to pick it up.",
        "sad": "As he dropped the letter, I bent down to pick it up.",
        "angry": "As he dropped the letter, I bent down to pick it up.",
        "disgust": "As he dropped the letter, I bent down to pick it up.",
        "fear": "As he dropped the letter, I bent down to pick it up.",
        "surprise": "As he dropped the letter, I bent down to pick it up.",
        "confused": "As he dropped the letter, I bent down to pick it up."
    },
    {
        "neutral": "Our eyes met briefly.",
        "happy": "Our eyes met briefly and he smiled.",
        "sad": "Our eyes met briefly and his gaze dropped.",
        "angry": "Our eyes met briefly and his glare sharpened.",
        "disgust": "Our eyes met briefly and he bristled.",
        "fear": "Our eyes met briefly and he flinched.",
        "surprise": "Our eyes met briefly and his eyes widened.",
        "confused": "Our eyes met briefly and he frowned."
    },
    {
        "neutral": "Nodding, he mumbled thanks, then turned away.",
        "happy": "Nodding, he murmured a warm thanks, then turned away.",
        "sad": "Shaking his head, he whispered a quiet thanks, then turned away.",
        "angry": "Scoffing, he muttered no thanks, then turned away.",
        "disgust": "Scoffing, he muttered a sharp thanks, then turned away.",
        "fear": "Nodding, he murmured a shaky thanks, then turned away.",
        "surprise": "Blinking, he mumbled thanks, then turned away.",
        "confused": "Shrugging, he mumbled something unclear, then turned away."
    },
    {
        "neutral": "I don’t know why, but the weight of that glance lingered.",
        "happy": "I don’t know why, but the weight of that glance lingered.",
        "sad": "I don’t know why, but the weight of that glance lingered.",
        "angry": "I don’t know why, but the weight of that glance lingered.",
        "disgust": "I don’t know why, but the weight of that glance lingered.",
        "fear": "I don’t know why, but the weight of that glance lingered.",
        "surprise": "I don’t know why, but the weight of that glance lingered.",
        "confused": "I don’t know why, but the weight of that glance lingered."
    },
    {
        "neutral": "I kept thinking: what was in that envelope?",
        "happy": "I kept thinking: what was in that envelope?",
        "sad": "I kept thinking: what was in that envelope?",
        "angry": "I kept thinking: what was in that envelope?",
        "disgust": "I kept thinking: what was in that envelope?",
        "fear": "I kept thinking: what was in that envelope?",
        "surprise": "I kept thinking: what was in that envelope?",
        "confused": "I kept thinking: what was in that envelope?"
    },
    {
        "neutral": "A tax reminder? A phone bill? A doctor’s appointment?",
        "happy": "A wedding invitation? A message from an old friend? A long-awaited “yes”?",
        "sad": "A job rejection? A goodbye? A chance missed?",
        "angry": "An unfair accusation? A broken promise? A final warning?",
        "disgust": "A cruel confession? A lie in ink? A betrayal?",
        "fear": "A negative medical result? A notice of eviction? A threat?",
        "surprise": "A forgotten letter? A secret revealed? A sudden offer?",
        "confused": "A message half-finished? A name he didn’t know? A letter meant for someone else?"
    },
    {
        "neutral": "The rain finally eased as the train pulled in. I got on.",
        "happy": "The rain finally eased as the train pulled in. I got on with a smile.",
        "sad": "The rain finally eased as the train pulled in. I got on with a heavy heart.",
        "angry": "The rain finally eased as the train pulled in. I got on, fists clenched.",
        "disgust": "The rain finally eased as the train pulled in. I got on, reluctantly.",
        "fear": "The rain finally eased as the train pulled in. I got on without looking back.",
        "surprise": "The rain finally eased as the train pulled in. I got on, still reeling.",
        "confused": "The rain finally eased as the train pulled in. I got on… the wrong one."
    },
    {
        "neutral": "Life continued.",
        "happy": "Life continued.",
        "sad": "Life continued.",
        "angry": "Life continued.",
        "disgust": "Life continued.",
        "fear": "Life continued.",
        "surprise": "Life continued.",
        "confused": "Life continued."
    },
    {
        "neutral": "But sometimes, I still think of that man in the rain—and how we all carry something unseen.",
        "happy": "But sometimes, I still think of that man in the rain—and how we all carry something worth sharing.",
        "sad": "But sometimes, I still think of that man in the rain—and how we all carry something quietly aching inside.",
        "angry": "But sometimes, I still think of that man in the rain—and how we all carry something waiting to explode.",
        "disgust": "But sometimes, I still think of that man in the rain—and how we all carry something we’d rather forget.",
        "fear": "But sometimes, I still think of that man in the rain—and how we all carry something we’re afraid to face.",
        "surprise": "But sometimes, I still think of that man in the rain—and how we all carry something we never expected.",
        "confused": "But sometimes, I still think of that man in the rain—and how we all carry something we can’t quite name."
    },
]

    sentence_index = 0
    last_spoken_time = 0
    min_delay_between_sentences = 3.0
    last_emotion = None
    same_emotion_count = 0

    try:
        while True:
            conn, addr = server_socket.accept()
            try:
                data = conn.recv(1024)
                if data:
                    try:
                        emotion = data.decode('utf-8').strip().lower()
                    except:
                        emotion = data.strip().lower()

                    print("[Emotion Receiver] Received emotion:", emotion)
                    current_time = time.time()

                    if emotion == last_emotion:
                        same_emotion_count += 1
                    else:
                        same_emotion_count = 1
                        last_emotion = emotion

                    should_speak = False
                    if same_emotion_count >= 5 and current_time - last_spoken_time >= min_delay_between_sentences:
                        should_speak = True
                    elif same_emotion_count == 1 and current_time - last_spoken_time >= min_delay_between_sentences:
                        should_speak = True

                    if should_speak and tts and sentence_index < len(emotion_to_phrase):
                        tags = get_speech_tags(emotion)
                        sentence_block = emotion_to_phrase[sentence_index]
                        phrase = sentence_block.get(emotion, sentence_block.get("neutral", ""))

                        speech = (
                            "\\vct={vct}\\"
                            "\\rspd={rspd}\\"
                            "\\vol={vol}\\"
                            "\\pau={pau}\\"
                            "{text}"
                        ).format(
                            vct=tags["vct"],
                            rspd=tags["rspd"],
                            vol=tags["vol"],
                            pau=tags["pau"],
                            text=phrase
                        )

                        try:
                            if animated_speech:
                                # Speak with animation
                                animated_speech.say(speech, "animations/Stand/Gestures/Hey_1")
                            else:
                                # fallback plain speech
                                tts.say(speech)

                            last_spoken_time = current_time
                            sentence_index += 1
                            same_emotion_count = 0  # reset after speaking

                            if sentence_index >= len(emotion_to_phrase):
                                print("[Emotion Receiver] End of story reached.")
                        except Exception as e:
                            print("[Emotion Receiver] TTS say error:", e)
                    else:
                        print("[Emotion Receiver] Waiting for new emotion or enough repetition...")

            except Exception as e:
                print("[Emotion Receiver] Error during connection:", e)
            finally:
                conn.close()
    except Exception as e:
        print("[Emotion Receiver] Error:", e)
    finally:
        server_socket.close()


# === Start Emotion Receiver Thread ===
emotion_thread = threading.Thread(target=emotion_receiver)
emotion_thread.setDaemon(True)
emotion_thread.start()

# === Start Video Streaming to Laptop ===
try:
    # Stop Basic Awareness (prevents autonomous head/body motion)
    awareness = ALProxy("ALBasicAwareness", PEPPER_IP, PEPPER_PORT)
    awareness.stopAwareness()

    # Stop tracking and unregister any previous targets
    tracker = ALProxy("ALTracker", PEPPER_IP, PEPPER_PORT)
    tracker.stopTracker()
    tracker.unregisterAllTargets()

    # Set head to face forward
    motion = ALProxy("ALMotion", PEPPER_IP, PEPPER_PORT)
    motion.setAngles(["HeadYaw", "HeadPitch"], [0.0, 0.0], 0.2)  # Head forward

    video_proxy = ALProxy("ALVideoDevice", PEPPER_IP, PEPPER_PORT)
    capture_id = video_proxy.subscribeCamera(camera_name, 0, resolution, color_space, fps)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((LAPTOP_IP, LAPTOP_PORT))
    print("[Video Sender] Connected to laptop at", LAPTOP_IP, LAPTOP_PORT)

    while True:
        image = video_proxy.getImageRemote(capture_id)
        if image is None:
            print("[Video Sender] No image received")
            time.sleep(0.1)
            continue

        width = image[0]
        height = image[1]
        array = image[6]

        np_arr = np.frombuffer(array, np.uint8)
        img = np_arr.reshape((height, width, 3))

        result, jpg = cv2.imencode('.jpg', img)
        if not result:
            print("[Video Sender] Failed to encode frame")
            continue

        jpg_bytes = jpg.tobytes()
        sock.sendall(struct.pack(">I", len(jpg_bytes)))
        sock.sendall(jpg_bytes)

        time.sleep(1.0 / fps)

except KeyboardInterrupt:
    print("Interrupted by user, exiting...")
except Exception as e:
    print("[Main] Error:", e)

finally:
    if capture_id:
        try:
            video_proxy.unsubscribe(capture_id)
        except Exception as e:
            print("Warning: could not unsubscribe cleanly:", e)
    if sock:
        sock.close()