# coding: utf-8
import qi
import time
import traceback

class PepperPitchTest:
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

    def speak_with_pitch_only(self):
        test_cases = [
            (0.5,  "This is very low."),
            (0.75, "This is moderately low."),
            (1.0,  "This is neutral."),
            (1.25, "This is slightly higher."),
            (1.5,  "This is high."),
        ]

        for pitch, sentence in test_cases:
            try:
                self.tts.setParameter("pitchShift", pitch)
                self.tts.setParameter("speed", 1.0)  # Constant speed
                print("[DEBUG] Speaking at pitch=%.2f: %s" % (pitch, sentence))
                self.animated_speech.say(sentence)
                time.sleep(1.0)
            except Exception as e:
                print("[ERROR] Failed to speak at pitch %.2f: %s" % (pitch, str(e)))
                traceback.print_exc()

if __name__ == "__main__":
    pepper_ip = "192.168.0.102"  # Replace with your Pepper's IP
    print("[DEBUG] Starting PepperPitchTest with IP %s" % pepper_ip)
    try:
        tester = PepperPitchTest(pepper_ip)
        tester.speak_with_pitch_only()
    except Exception as e:
        print("[FATAL] Could not run pitch test: %s" % str(e))
        traceback.print_exc()
