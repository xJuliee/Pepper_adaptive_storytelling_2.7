# coding: utf-8
import qi
import time
import threading
import random
import traceback

class PepperDynamicPitchSpeaker(object):
    def __init__(self, robot_ip, port=9559):
        self.robot_ip = robot_ip
        self.port = port
        self.session = None
        self.tts = None
        self.face_char = None
        self.memory = None
        self.awareness = None
        self.animated_speech = None

        # Establish a single persistent connection and initialize services
        self.connect_and_init_services()

        self.running = True
        self.current_emotion = None
        self.last_emotion_update = 0
        self.emotion_update_interval = 5.0  # seconds between updates
        self.lock = threading.Lock()

        self.animations = {
            "happy": ["^start(animations/Moods/Positive/Pepper/Kisses)"],
            # "sad": ["^start(animations/Stand/Gestures/Frustration_1)"],
            # "angry": ["^start(animations/Stand/Gestures/Angry_1)"],
            # "surprised": ["^start(animations/Stand/Gestures/Surprised_1)"],
        }

    def connect_and_init_services(self):
        """Connect to Pepper and initialize services if not connected."""
        try:
            if self.session:
                try:
                    self.session.close()
                except Exception:
                    pass
            self.session = qi.Session()
            self.session.connect("tcp://%s:%d" % (self.robot_ip, self.port))
            print("[DEBUG] Connected to Pepper at %s:%d" % (self.robot_ip, self.port))

            self.tts = self.session.service("ALTextToSpeech")
            self.face_char = self.session.service("ALFaceCharacteristics")
            self.memory = self.session.service("ALMemory")
            self.awareness = self.session.service("ALBasicAwareness")
            self.animated_speech = self.session.service("ALAnimatedSpeech")

            print("[DEBUG] All NAOqi services initialized successfully.")
        except Exception as e:
            print("[ERROR] Failed to connect or initialize services: %s" % str(e))
            traceback.print_exc()
            raise

    def is_connected(self):
        try:
            if self.memory:
                self.memory.ping()
                return True
            else:
                return False
        except Exception:
            return False

    def reconnect(self):
        print("[WARNING] Attempting to reconnect to Pepper...")
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts and not self.is_connected():
            try:
                self.connect_and_init_services()
                print("[DEBUG] Reconnection successful.")
                return True
            except Exception as e:
                attempt += 1
                print("[ERROR] Reconnection attempt %d failed: %s" % (attempt, str(e)))
                traceback.print_exc()
                time.sleep(2)
        print("[ERROR] Reconnection attempts exceeded maximum tries.")
        return False

    def start_awareness(self):
        if not self.is_connected():
            if not self.reconnect():
                print("[ERROR] Cannot start awareness, no connection.")
                return
        try:
            self.awareness.startAwareness()
            print("[DEBUG] Awareness started.")
        except Exception as e:
            print("[ERROR] Failed to start awareness: %s" % str(e))

    def stop_awareness(self):
        if not self.is_connected():
            print("[WARN] Cannot stop awareness, no connection.")
            return
        try:
            self.awareness.stopAwareness()
            print("[DEBUG] Awareness stopped.")
        except Exception as e:
            print("[ERROR] Failed to stop awareness: %s" % str(e))

    def detect_emotion_loop(self):
        while self.running:
            if not self.is_connected():
                if not self.reconnect():
                    time.sleep(2)
                    continue

            try:
                ids = self.memory.getData("PeoplePerception/PeopleList")
                if not ids:
                    print("[DEBUG] No people detected.")
                    with self.lock:
                        self.current_emotion = "neutral"  # use neutral instead of None
                elif len(ids) > 1:
                    print("[DEBUG] Multiple people detected. Skipping emotion detection.")
                    with self.lock:
                        self.current_emotion = "neutral"
                else:
                    person_id = ids[0]
                    now = time.time()
                    if now - self.last_emotion_update >= self.emotion_update_interval:
                        print("[DEBUG] Analyzing face characteristics for ID: %s" % str(person_id))
                        self.face_char.analyzeFaceCharacteristics(person_id)
                        time.sleep(3.0)
                        props = self.memory.getData(
                            "PeoplePerception/Person/%s/ExpressionProperties" % str(person_id)
                        )
                        print("[DEBUG] Expression properties: %s" % str(props))
                        emotions = ["neutral", "happy", "surprised", "angry", "sad"]
                        if not props or len(props) != len(emotions):
                            print("[WARN] Expression properties length mismatch or empty, using default neutral values.")
                            props = [1.0, 0.0, 0.0, 0.0, 0.0]

                        emotion_scores = dict(zip(emotions, props))
                        detected_emotion = max(emotion_scores, key=emotion_scores.get)
                        print("[DEBUG] Detected emotion: %s" % detected_emotion)

                        with self.lock:
                            if self.current_emotion != detected_emotion:
                                self.current_emotion = detected_emotion
                                self.last_emotion_update = now
                                print("[DEBUG] Emotion updated to: %s" % detected_emotion)
                            else:
                                print("[DEBUG] Emotion unchanged: %s" % detected_emotion)
                time.sleep(1)
            except Exception as e:
                print("Emotion detection error: %s" % str(e))
                traceback.print_exc()
                time.sleep(1)

    def speak_with_dynamic_pitch(self, text):
        if not self.is_connected():
            if not self.reconnect():
                print("[ERROR] Cannot speak, no connection.")
                return

        sentences = text.split('. ')
        for sentence in sentences:
            if not sentence.strip() or not self.running:
                continue

            with self.lock:
                emotion = self.current_emotion
            if emotion is None:
                emotion = "neutral"  # replace None with neutral here too

            pitch = 1.0
            speed = 1.0
            if emotion == "happy":
                pitch = 1.5
            elif emotion == "angry":
                pitch = 0.7
            elif emotion == "sad":
                speed = 0.7
            elif emotion == "surprised":
                speed = 1.2

            try:
                self.tts.setParameter("pitchShift", pitch)
                self.tts.setParameter("speed", speed)
                print("[DEBUG] TTS parameters set: pitch=%.2f, speed=%.2f" % (pitch, speed))
            except Exception as e:
                print("TTS parameter error: %s" % str(e))
                traceback.print_exc()

            animation = ""
            if emotion in self.animations:
                animation = random.choice(self.animations[emotion])
            animated_sentence = "%s %s" % (animation, sentence.strip())
            print("Saying with emotion '%s': %s" % (emotion, animated_sentence))
            try:
                self.animated_speech.say(animated_sentence)
            except Exception as e:
                print("AnimatedSpeech error: %s" % str(e))
                traceback.print_exc()

            time.sleep(0.5)

    def run(self, text):
        self.start_awareness()
        detection_thread = threading.Thread(target=self.detect_emotion_loop)
        detection_thread.setDaemon(True)
        detection_thread.start()
        try:
            while self.running:
                self.speak_with_dynamic_pitch(text)
                time.sleep(1)
        except KeyboardInterrupt:
            print("Interrupted by user, stopping...")
            self.running = False
        except Exception as e:
            print("Unexpected error in run loop: %s" % str(e))
            traceback.print_exc()
        finally:
            self.running = False
            detection_thread.join()
            self.stop_awareness()
            print("[DEBUG] Program terminated gracefully.")

if __name__ == "__main__":
    pepper_ip = "192.168.0.102"  # Replace with your Pepper's IP
    print("[DEBUG] Starting PepperDynamicPitchSpeaker with IP %s" % pepper_ip)
    try:
        speaker = PepperDynamicPitchSpeaker(pepper_ip)
        long_text = (
            "Hello! This is Pepper speaking. "
            "I am happy to talk with you. "
            "If you look happy, I will raise my voice pitch. "
            "If you're sad, I'll slow down. "
            "Let's see if it works well!"
        )
        speaker.run(long_text)
    except Exception as e:
        print("[FATAL] Could not start speaker: %s" % str(e))
        traceback.print_exc()
