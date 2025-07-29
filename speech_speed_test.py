# coding: utf-8
import qi
import time
import traceback

class PepperPauseTest:
    def __init__(self, robot_ip, port=9559):
        self.robot_ip = robot_ip
        self.port = port
        self.session = None
        self.tts = None
        self.animated_speech = None
        self.connect_services()

    def connect_services(self):
        try:
            self.session = qi.Session()
            self.session.connect("tcp://%s:%d" % (self.robot_ip, self.port))
            print("[DEBUG] Connected to Pepper at %s:%d" % (self.robot_ip, self.port))

            self.tts = self.session.service("ALTextToSpeech")
            self.animated_speech = self.session.service("ALAnimatedSpeech")
        except Exception as e:
            print("[ERROR] Failed to connect or initialize services: %s" % str(e))
            traceback.print_exc()
            raise

    def speak_with_pauses(self):
        pause_tests = [
            (100,  "This is a \\PAU=100\\ sound."),
            (300,  "This is a \\PAU=300\\ sound."),
            (600,  "This is a \\PAU=600\\ sound."),
            (1000, "This is a \\PAU=1000\\ sound."),
        ]

        for pause_duration, sentence in pause_tests:
            try:
                print("[DEBUG] Speaking with pause=%d ms: %s" % (pause_duration, sentence))
                self.animated_speech.say(sentence)
                time.sleep(1.5)
            except Exception as e:
                print("[ERROR] Failed to speak with pause %d: %s" % (pause_duration, str(e)))
                traceback.print_exc()

if __name__ == "__main__":
    pepper_ip = "192.168.0.102"  # Replace with your Pepper's IP
    print("[DEBUG] Starting PepperPauseTest with IP %s" % pepper_ip)
    try:
        tester = PepperPauseTest(pepper_ip)
        tester.speak_with_pauses()
    except Exception as e:
        print("[FATAL] Could not run pause test: %s" % str(e))
        traceback.print_exc()
