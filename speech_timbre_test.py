# coding: utf-8
import qi
import time
import traceback

class PepperVoiceShapeTest:
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

    def speak_with_voice_shapes(self):
        vct_tests = [
            (80,  "\\VCT=80\\ This is a low voice. \\RST\\"),
            (100, "\\VCT=100\\ This is the default voice. \\RST\\"),
            (120, "\\VCT=120\\ This is a higher-pitched voice. \\RST\\"),
            (140, "\\VCT=140\\ This is a very high voice. \\RST\\")
        ]

        for vct_value, sentence in vct_tests:
            try:
                print("[DEBUG] Speaking with VCT=%d: %s" % (vct_value, sentence))
                self.animated_speech.say(sentence)
                time.sleep(1.5)
            except Exception as e:
                print("[ERROR] Failed to speak with VCT %d: %s" % (vct_value, str(e)))
                traceback.print_exc()

if __name__ == "__main__":
    pepper_ip = "192.168.0.102"  # Replace with your Pepper's IP
    print("[DEBUG] Starting PepperVoiceShapeTest with IP %s" % pepper_ip)
    try:
        tester = PepperVoiceShapeTest(pepper_ip)
        tester.speak_with_voice_shapes()
    except Exception as e:
        print("[FATAL] Could not run voice shape test: %s" % str(e))
        traceback.print_exc()
