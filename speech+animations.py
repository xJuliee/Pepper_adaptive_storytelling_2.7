# coding: utf-8
import qi
import time
import threading
import traceback

class PepperDynamicPitchSpeaker(object):
    def __init__(self, robot_ip, port=9559):
        self.robot_ip = robot_ip  # IP address of the Pepper robot
        self.port = port  # Port number used to connect to Pepper (default is 9559)
        self.session = None  # Holds the NAOqi session object
        self.tts = None  # Text-to-Speech service
        self.face_char = None  # Face characteristics analysis service
        self.memory = None  # ALMemory service (reading Pepper's internal data)
        self.awareness = None  # Awareness service (tracking people)
        self.animated_speech = None  # Service to speak with gestures/animations

        self.connect_and_init_services()  # Connect and initialize all services

        self.running = True  # Main loop control flag
        self.current_emotion = None  # Tracks the currently detected emotion
        self.last_emotion_update = 0  # Timestamp of the last emotion update
        self.emotion_update_interval = 5.0  # Time in seconds to wait before detecting a new emotion
        self.lock = threading.Lock()  # Used to safely share data between threads (e.g., emotion changes)

        self.last_animation_time = 0  # Timestamp of the last animation trigger
        self.animation_cooldown = 5.5  # Minimum time in seconds between two animations
        self.animation_index = {emotion: 0 for emotion in ["happy", "sad", "angry", "surprised", "neutral"]}
        # Tracks which animation to play next for each emotion (used to cycle animations)

        # Emotion-specific animation list
        self.animations = {
            "happy": [
                "^start(animations/Stand/Gestures/Happy_1)",
                "^start(animations/Stand/Gestures/WideOpenBothHands_1)",
                "^start(animations/Stand/Gestures/GoToStance_Exclamation_Center)"
            ],
            "sad": [
                "^start(animations/Stand/Gestures/SlowBowWithArms_1)",
                "^start(animations/Stand/Gestures/Confused_1)",
                "^start(animations/Stand/Gestures/RightArmUpAndDownWithBump_HeadShake_1)"
            ],
            "angry": [
                "^start(animations/Stand/Gestures/GoToStance_Enumeration_Center)",
                "^start(animations/Stand/Gestures/GoToStance_Negation_Center)",
                "^start(animations/Stand/Gestures/CircleBothArmsLeaningFront_1)",
                "^start(animations/Stand/Gestures/GoToStance_SpaceAndTime_LeanRight)"
            ],
            "surprised": [
                "^start(animations/Stand/Gestures/LittleArmsBump_1)",
                "^start(animations/Stand/Gestures/StrongBothArmsUpAndDown_LeanLeft_1)",
                "^start(animations/Stand/Gestures/BothArmsUpAndDown_HeadShake_1)"
            ],
            "neutral": [
                "^start(animations/Stand/Gestures/Chill_1)"
            ]
        }

    def connect_and_init_services(self):
        self.session = qi.Session()  # Create a new NAOqi session object
        self.session.connect("tcp://%s:%d" % (self.robot_ip, self.port))
        # Initialize required NAOqi services
        self.tts = self.session.service("ALTextToSpeech") # Speaking using Pepper’s voice
        self.face_char = self.session.service("ALFaceCharacteristics") # Analyzes facial features to detect emotions
        self.memory = self.session.service("ALMemory") # Access Pepper’s internal memory to read sensor data (like expressions)
        self.awareness = self.session.service("ALBasicAwareness") # Handles Pepper’s ability to detect and track people
        self.animated_speech = self.session.service("ALAnimatedSpeech") # Allows Pepper to speak using animations and gestures
        print("[DEBUG] All NAOqi services initialized successfully.")

    def detect_emotion_loop(self):
        while self.running:
            try:
                ids = self.memory.getData("PeoplePerception/PeopleList")  # Get list of detected people
                if not ids or len(ids) != 1:
                    # Set to neutral if no one OR multiple people are detected
                    with self.lock:
                        self.current_emotion = "neutral"
                else:
                    person_id = ids[0]  # Only one person detected, proceed
                    now = time.time()
                    if now - self.last_emotion_update >= self.emotion_update_interval:
                        self.face_char.analyzeFaceCharacteristics(person_id)  # Trigger emotion analysis
                        time.sleep(3.0)  # Allow time for analysis to complete

                        props = self.memory.getData("PeoplePerception/Person/%s/ExpressionProperties" % str(person_id))
                        # Get emotion probabilities from memory

                        emotions = ["neutral", "happy", "surprised", "angry", "sad"]
                        if not props or len(props) != len(emotions):
                            props = [1.0, 0.0, 0.0, 0.0, 0.0]  # Fallback to neutral if invalid

                        scores = dict(zip(emotions, props))  # Map emotions to their scores
                        with self.lock:
                            self.current_emotion = max(scores, key=scores.get)  # Set highest scoring emotion
                            self.last_emotion_update = now  # Update timestamp
                time.sleep(1)  # Wait before next loop
            except Exception:
                traceback.print_exc()
                time.sleep(1)

    def speak_with_dynamic_pitch(self, text):
        sentences = text.split('. ')  # Split text into individual sentences
        for sentence in sentences:
            if not sentence.strip() or not self.running:
                continue  # Skip empty sentences or if program is stopping

            with self.lock:
                emotion = self.current_emotion or "neutral"  # Use current detected emotion, default to neutral

            # Set voice pitch and VCT modifier based on emotion
            pitch, vct = 1.0, "\\RST\\"
            if emotion == "happy":
                pitch, vct = 1.5, "\\VCT=120\\"
            elif emotion == "angry":
                pitch, vct = 0.5, "\\VCT=80\\"
            elif emotion == "sad":
                pitch, vct = 0.75, "\\VCT=100\\"
            elif emotion == "surprised":
                pitch, vct = 1.1, "\\VCT=110\\"

            try:
                self.tts.setParameter("pitchShift", pitch)  # Apply pitch change
                print("[DEBUG] TTS parameters set: pitch=%.2f, VCT=%s" % (pitch, vct))
            except Exception:
                traceback.print_exc()

            # Trigger animation if cooldown has passed and emotion is valid
            now = time.time()
            animation = ""
            if emotion in self.animations and (now - self.last_animation_time >= self.animation_cooldown):
                anim_list = self.animations[emotion]
                index = self.animation_index[emotion] % len(anim_list)  # Get next animation index cyclically
                animation = anim_list[index]  # Pick animation
                self.animation_index[emotion] += 1  # Update index for next round
                self.last_animation_time = now  # Reset cooldown timer
                print("[DEBUG] Playing animation for emotion: %s" % emotion)
            else:
                print("[DEBUG] Skipping animation: cooldown not met or invalid emotion.")

            # Combine animation trigger, voice pitch command, and sentence
            animated_sentence = "%s %s %s" % (animation, vct, sentence.strip())
            print("Saying with emotion '%s': %s" % (emotion, animated_sentence))
            try:
                self.animated_speech.say(animated_sentence)  # Speak the sentence with animation
            except Exception:
                traceback.print_exc()

            time.sleep(3.0)  # Wait before proceeding to next sentence

    def run(self, text):
        self.awareness.startAwareness()  # Enable Pepper's basic awareness

        # Start emotion detection loop in a separate background thread
        detection_thread = threading.Thread(target=self.detect_emotion_loop)
        detection_thread.setDaemon(True)  # Allows thread to exit when main program ends
        detection_thread.start()

        try:
            while self.running:
                self.speak_with_dynamic_pitch(text)  # Speak text with emotional pitch and animation
                time.sleep(2.0)  # Small delay between repetitions
        except KeyboardInterrupt:
            print("Interrupted by user")  # Handle Ctrl+C
        finally:
            self.running = False  # Signal all loops to stop
            detection_thread.join()  # Wait for detection thread to finish
            self.awareness.stopAwareness()  # Stop Pepper’s awareness
            print("[DEBUG] Program terminated")

if __name__ == "__main__":
    pepper_ip = "192.168.0.102"  # IP address of the Pepper robot
    print("[DEBUG] Starting PepperDynamicPitchSpeaker with IP %s" % pepper_ip)
    try:
        speaker = PepperDynamicPitchSpeaker(pepper_ip)  # Create instance
        long_text = (
            "Hello! This is Pepper speaking. "
            "I am happy to talk with you. "
            "If you look happy, I will raise my voice pitch. "
            "If you're sad, I'll slow down. "
            "Let's see if it works well!"
        )
        speaker.run(long_text)  # Start main loop
    except Exception as e:
        print("[FATAL] Could not start speaker: %s" % str(e))  # Handle startup errors
        traceback.print_exc()