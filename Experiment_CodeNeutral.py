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

# === Initialize TTS service ===
try:
    tts = ALProxy("ALTextToSpeech", PEPPER_IP, PEPPER_PORT)
    tts.setLanguage("English")
except Exception as e:
    print("[TTS Init] Failed to connect to ALTextToSpeech:", e)
    tts = None

# === Emotion-based Speech Tagging ===
def get_speech_tags(emotion):
    settings = {
        "neutral": {"vct":100, "rspd":100, "vol":80, "pau":100}
    }
    return settings["neutral"]

# === Emotion Receiving Function with Speech ===
def emotion_receiver():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PEPPER_RECEIVE_PORT))
    server_socket.listen(5)
    print("[Emotion Receiver] Listening on port", PEPPER_RECEIVE_PORT)

    # Map emotion to fixed speech phrases
    emotion_to_phrase = [
    {
        "neutral": "It was raining that morning."
    },
    {
        "neutral": "I stood on the platform, clutching the umbrella."
    },
    {
        "neutral": "The train was late."
    },
    {
        "neutral": "People huddled under the awning, quiet."
    },
    {
        "neutral": "I almost missed it—the man across from me, fumbling with an envelope, his hands shaking slightly."
    },
    {
        "neutral": "He looked nonchalant. Casual, even."
    },
    {
        "neutral": "As he dropped the letter, I bent down to pick it up."
    },
    {
        "neutral": "Our eyes met briefly."
    },
    {
        "neutral": "Nodding, he mumbled thanks, then turned away."
    },
    {
        "neutral": "I don’t know why, but the weight of that glance lingered."
    },
    {
        "neutral": "The rain finally eased as the train pulled in."
    },
]

    sentence_index = 0  # define globally

    try:
        last_spoken_time = 0
        min_delay_between_sentences = 3.0  # seconds (adjust as needed)
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

                    global sentence_index
                    current_time = time.time()

                    if current_time - last_spoken_time < min_delay_between_sentences:
                        print("[Emotion Receiver] Waiting to speak next sentence...")
                        continue  # Don't proceed yet

                    if tts and sentence_index < len(emotion_to_phrase):
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
                            tts.say(speech)
                            last_spoken_time = current_time  # update time
                            sentence_index += 1
                            if sentence_index >= len(emotion_to_phrase):
                                print("[Emotion Receiver] End of story reached.")
                        except Exception as e:
                            print("[Emotion Receiver] TTS say error:", e)
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
    # Disable autonomous behavior
    awareness = ALProxy("ALBasicAwareness", PEPPER_IP, PEPPER_PORT)
    awareness.stopAwareness()

    # Optional: Stop any tracking behavior
    tracker = ALProxy("ALTracker", PEPPER_IP, PEPPER_PORT)
    tracker.stopTracker()

    # Subscribe to camera
    video_proxy = ALProxy("ALVideoDevice", PEPPER_IP, PEPPER_PORT)
    capture_id = video_proxy.subscribeCamera(camera_name, 0, resolution, color_space, fps)

    # Connect to laptop
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

        # Convert raw bytes to numpy array
        np_arr = np.frombuffer(array, np.uint8)
        img = np_arr.reshape((height, width, 3))

        # Encode frame as JPEG
        result, jpg = cv2.imencode('.jpg', img)
        if not result:
            print("[Video Sender] Failed to encode frame")
            continue

        jpg_bytes = jpg.tostring()

        # Send JPEG size header and frame
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