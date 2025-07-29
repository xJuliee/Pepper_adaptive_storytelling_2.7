# -*- coding: utf-8 -*-
import socket
import threading
import time
import traceback
import qi

PEPPER_IP = "192.168.0.101"
PEPPER_PORT = 9559
EMOTION_PORT = 6001

class PepperDynamicPitchSpeaker(object):
    def __init__(self, robot_ip, port=9559):
        self.robot_ip = robot_ip
        self.port = port
        self.session = qi.Session()
        self.session.connect("tcp://{}:{}".format(self.robot_ip, self.port))

        self.tts = self.session.service("ALTextToSpeech")
        self.animated_speech = self.session.service("ALAnimatedSpeech")
        self.awareness = self.session.service("ALBasicAwareness")

        self.current_emotion = "neutral"
        self.running = True
        self.lock = threading.Lock()
        self.animation_index = {
            "happy": 0, "sad": 0, "angry": 0, "surprised": 0, "neutral": 0
        }

        self.animations = {
            "happy": ["^run(animations/Stand/Gestures/Happy_1)"],
            "sad": ["^run(animations/Stand/Gestures/SlowBowWithArms_1)"],
            "angry": ["^run(animations/Stand/Gestures/GoToStance_Enumeration_Center)"],
            "surprised": ["^run(animations/Stand/Gestures/LittleArmsBump_1)"]
        }

    def get_next_animation(self, emotion):
        if emotion in self.animations:
            index = self.animation_index[emotion] % len(self.animations[emotion])
            self.animation_index[emotion] += 1
            return self.animations[emotion][index]
        return ""

    def prepare_speech_parameters(self, emotion):
        pitch, vct = 1.0, "\\RST\\"
        if emotion == "happy":
            pitch, vct = 1.5, "\\VCT=120\\"
        elif emotion == "angry":
            pitch, vct = 0.5, "\\VCT=80\\"
        elif emotion == "sad":
            pitch, vct = 0.75, "\\VCT=100\\"
        elif emotion == "surprised":
            pitch, vct = 1.1, "\\VCT=110\\"
        return pitch, vct

    def speak_with_emotion(self, text):
        self.lock.acquire()
        emotion = self.current_emotion
        self.lock.release()

        pitch, vct = self.prepare_speech_parameters(emotion)
        try:
            self.tts.setParameter("pitchShift", pitch)
        except Exception:
            traceback.print_exc()

        anim = self.get_next_animation(emotion)
        final_text = "{} {} {}".format(anim, vct, text)

        print("[DEBUG] Speaking: {}".format(final_text))
        try:
            self.animated_speech.say(final_text)
        except Exception:
            traceback.print_exc()

    def run(self, text):
        self.awareness.startAwareness()
        try:
            while self.running:
                self.speak_with_emotion(text)
                time.sleep(5)
        except KeyboardInterrupt:
            pass
        finally:
            self.awareness.stopAwareness()

def emotion_server(speaker, host='', port=6001):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print("[DEBUG] Emotion server listening on port {}".format(port))

    while True:
        conn, addr = server.accept()
        try:
            data = conn.recv(1024)
            if data:
                emotion = data.strip()
                if isinstance(emotion, bytes):
                    emotion = emotion.decode('utf-8')
                print("[DEBUG] Received emotion: {}".format(emotion))
                speaker.lock.acquire()
                speaker.current_emotion = emotion
                speaker.lock.release()
            conn.sendall("OK\n")
        except Exception as e:
            print("[ERROR] While receiving emotion: {}".format(e))
        finally:
            conn.close()

if __name__ == "__main__":
    speaker = PepperDynamicPitchSpeaker(PEPPER_IP)
    emotion_thread = threading.Thread(target=emotion_server, args=(speaker,))
    emotion_thread.setDaemon(True)  # Correct way in Python 2.7
    emotion_thread.start()

    sample_text = (
        "Hello! I am Pepper. "
        "I will speak with emotion based on how you look. "
        "Let’s see what emotion you send me!"
    )
    speaker.run(sample_text)