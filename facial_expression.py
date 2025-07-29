# coding: utf-8
import time
import qi
from naoqi import ALProxy

class PepperEmotionRecognizer(object):
    def __init__(self, robot_ip="192.168.0.102", port=9559, confidence_threshold=0.3):
        self.robot_ip = robot_ip
        self.port = port

        # Setup qi session connection
        self.session = qi.Session()
        try:
            self.session.connect("tcp://{}:{}".format(self.robot_ip, self.port))
        except RuntimeError:
            print("Can't connect to Pepper at ip {} on port {}".format(self.robot_ip, self.port))
            exit(1)

        # Use ALProxy for services in Python 2.7 (qi service access is limited)
        self.motion = ALProxy("ALMotion", self.robot_ip, self.port)
        self.awareness = ALProxy("ALBasicAwareness", self.robot_ip, self.port)
        self.face_char = ALProxy("ALFaceCharacteristics", self.robot_ip, self.port)
        self.memory = ALProxy("ALMemory", self.robot_ip, self.port)
        self.tts = ALProxy("ALTextToSpeech", self.robot_ip, self.port)

        # Thresholds for emotions
        self.confidence = confidence_threshold
        self.thresh = {
            "neutral": self.confidence + 0.15,
            "happy": self.confidence,
            "surprised": self.confidence + 0.05,
            "angry": self.confidence + 0.2,
            "sad": self.confidence + 0.15
        }
        self.emotions = ["neutral", "happy", "surprised", "angry", "sad"]

    def wake_up(self):
        print("[INFO] Waking up Pepper...")
        self.motion.wakeUp()

    def start_awareness(self):
        print("[INFO] Starting Basic Awareness...")
        self.awareness.setEngagementMode("FullyEngaged")
        self.awareness.setTrackingMode("Head")
        self.awareness.setStimulusDetectionEnabled("People", True)
        self.awareness.setStimulusDetectionEnabled("Sound", True)
        self.awareness.setStimulusDetectionEnabled("Movement", True)
        self.awareness.startAwareness()

    def stop_awareness(self):
        print("[INFO] Stopping Basic Awareness...")
        self.awareness.stopAwareness()

    def get_expression(self, timeout=10):
        print("[INFO] Detecting facial expression...")
        start_time = time.time()
        counter = 0
        tProperties = [0.0] * 5  # neutral, happy, surprised, angry, sad

        while time.time() - start_time < timeout:
            try:
                ids = self.memory.getData("PeoplePerception/PeopleList")
                if len(ids) == 0:
                    print("[WARN] No face detected.")
                    time.sleep(0.5)
                    continue
                elif len(ids) > 1:
                    print("[WARN] Multiple faces detected.")
                    time.sleep(0.5)
                    continue

                person_id = ids[0]
                self.face_char.analyzeFaceCharacteristics(person_id)
                time.sleep(0.2)
                props = self.memory.getData("PeoplePerception/Person/{}/ExpressionProperties".format(person_id))
                for i in range(5):
                    tProperties[i] += props[i]
                counter += 1

                if counter == 4:
                    break
            except Exception as e:
                print("[ERROR] Exception while reading face expression: {}".format(e))
                time.sleep(0.5)

        if counter < 4:
            print("[ERROR] Not enough samples collected.")
            return None

        # Average the emotion scores
        tProperties = [val / 4 for val in tProperties]

        recognized = [0.0] * 5
        for idx, emo in enumerate(self.emotions):
            if tProperties[idx] > self.thresh[emo]:
                recognized[idx] = tProperties[idx]

        if max(recognized) == 0:
            return None

        return self.emotions[recognized.index(max(recognized))]

    def say_emotion(self, emotion):
        if emotion:
            message = "You look " + emotion
        else:
            message = "I don't know."
        print("[SAYING] " + message)
        self.tts.say(message)

    def run(self):
        self.wake_up()
        self.start_awareness()
        time.sleep(2)  # Allow awareness to engage
        emotion = self.get_expression()
        self.stop_awareness()
        self.say_emotion(emotion)


if __name__ == "__main__":
    recognizer = PepperEmotionRecognizer(
        robot_ip="192.168.0.102",  # Replace with your Pepper's IP address
        port=9559,
        confidence_threshold=0.3
    )
    recognizer.run()
