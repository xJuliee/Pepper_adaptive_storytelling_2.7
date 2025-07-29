# -*- coding: utf-8 -*-

from naoqi import ALProxy
import time

PEPPER_IP = "PEPPER_IP"  # Replace with your Pepper's IP

tts = ALProxy("ALTextToSpeech", PEPPER_IP, 9559)
anim = ALProxy("ALAnimationPlayer", PEPPER_IP, 9559)
memory = ALProxy("ALMemory", PEPPER_IP, 9559)
face_detection = ALProxy("ALFaceDetection", PEPPER_IP, 9559)
face_char = ALProxy("ALFaceCharacteristics", PEPPER_IP, 9559)

face_detection.subscribe("storytelling")

stories = {
    "neutral": [
        "Once upon a time, in a cheerful little town filled with sunshine and laughter, lived a very talkative and very helpful character named... The Hand.",
        "“Greetings, Traveller!” the Hand beamed. “Welcome to our lovely little town! It’s cozy, friendly, and completely safe! Well... mostly.”",
        "Just then—ROOOAARRR! A big green dinosaur burst onto the square with a growl, a grumble, and an odd little coo.",
        "The Hand froze. “Uh-oh... That’s new. Maybe if we stay very still, it’ll go away?”",
        # 4 index
        "CRASH! BOOM! STOMP! The Dino stormed into a bakery.",
        "“The bakery? But all they have is... bread?” The Hand blinked.",
        "Moments later, the Dino reappeared, a giant fluffy loaf clutched lovingly in its claws. It plopped down, munching happily.",
        "The Hand gasped. “So that’s what it wanted! Dinosaurs love bread!”",
        "RAAARGH! The Dino finished the loaf... and got angry again.",
        "“Oh no!” cried the Hand. “It’s wrecking everything!”",
        "“Wait—maybe if we give it more bread, it’ll calm down!”",
        "You gave it a pretzel, and the Dino gobbled it up.",
        "“Success!” cheered The Hand.",
        "But soon the Dino got hungry again. The next treat? A loaf with zebra stripes.",
        "The Hand frowned. “Wait, that’s just white bread… with style?”",
        # 15 index
        "The Dino didn’t care. It munched it down.",
        "Then came a giant sourdough—too big for The Hand to carry alone.",
        "“Do you know someone big and strong?” asked The Hand. “Like a grown-up?”",
        "With some teamwork, the two of you hurled the sourdough to the hungry creature.",
        "The Dino caught it and munched. “Mmm…”",
        "But not long after, it came back—pacing, sniffing, growling.",
        "So you found a fancy baguette and tossed it high.",
        "The Dino caught it mid-air. “My name is Levi,” it said. “And I don’t even like baguettes.” Then shrugged... and ate it anyway.",
        "More breads followed: a dino-shaped bread! A mysterious swirly loaf! And finally… cake.",
        "Fluffy, sweet, magical cake, baked just for Levi by a friendly baker.",
        # 25 index
        "Levi bit into it—and began to glow!",
        "Lights burst from his belly, and Levi transformed into a Dragon!",
        # 26 index
        "“I have wings!” he shouted surprised.",
        "The baker laughed. “Now you can bake your own bread—no more smashing bakeries!”",
        "Levi nodded. “Thank you, Baker. And thank you, Hand. And you too, Traveller!”",
        "He coughed up a slightly soggy sourdough and handed it to The Hand.",
        "“Oh… uhm… thank you,” said The Hand.",
        "Levi gave one last roar and flew off toward Dino-land.",
        "The Hand turned to the Traveller. “Well, that was... something.”",
        "The Baker stepped in. “You’ve earned a reward. I’ve got fresh bread for you both!”",
        "“And maybe next time,” said The Hand, “we’ll visit a town *without* cake-powered flying dinosaurs.”"
    ],
    "happy": [
        "CRASH! BOOM! STOMP! The Dino danced into the bakery with glee.",
        "The Dino wagged its tail and munched it down happily.",
        "Levi bit into it—and giggled with delight as he began to glow!",
        "“Wheee! I have wings!” he shouted with joy.",
    ],
    "sad": [
        "CRASH! BOOM! STOMP! The Dino slumped into the bakery with a sigh.",
        "The Dino became very sad. It munched it down slowly...",
        "Levi bit into it—and tears welled in his eyes as he began to glow.",
        "“I have wings…” he whispered softly, almost in disbelief.",
    ],
    "surprised": [
        "CRASH! BOOM! STOMP! The Dino stumbled into the bakery in a daze!",
        "The Dino looked stunned. It munched it down with wide eyes.",
        "Levi bit into it—and gasped as he began to glow!",
        "“Whoa! I have wings?!” he yelled, eyes wide with wonder.",
    ],
    "angry": [
        "CRASH! BOOM! STOMP! The Dino stormed into the bakery, snarling.",
        "The Dino growled and tore the bread apart, munching it down fiercely.",
        "Levi bit into it—and roared as he began to glow, flames licking the air.",
        "“Finally! Wings!” he bellowed, still crackling with leftover rage.",
    ]
}

# This function merges the base story with the emotion-specific lines by replacing key sentences
def merge_emotion_story(base_story, emotion_story):
    override_indices = [4, 15, 25, 26]
    merged_story = base_story[:]
    for i, line in enumerate(emotion_story):
        if i < len(override_indices):
            merged_story[override_indices[i]] = line
    return merged_story

current_emotion = "neutral"
current_story = stories["neutral"]
sentence_index = 0

def speak_with_animation(text, emotion):
    anim_tags = {
        "happy": "animations/Stand/Gestures/Hey_1",
        "sad": "animations/Stand/Emotions/Negative/Sad_1",
        "neutral": "animations/Stand/Gestures/Explain_1",
        "surprised": "animations/Stand/Gestures/Surprised_1",
        "angry": "animations/Stand/Emotions/Negative/Angry_1"
    }
    anim_tag = anim_tags.get(emotion, "")
    if anim_tag:
        full_text = "^start({}) {} ^wait({})".format(anim_tag, text, anim_tag)
    else:
        full_text = text
    tts.say(full_text)

def listen_for_continue(timeout=10):
    print("Waiting for user input to continue (press Enter)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            if raw_input() == "":
                return True
        except EOFError:
            pass
    return False

def get_dominant_emotion():
    ids = memory.getData("PeoplePerception/PeopleList")
    if not ids or len(ids) != 1:
        return "neutral"

    face_id = ids[0]
    face_char.analyzeFaceCharacteristics(face_id)
    time.sleep(0.3)

    props = memory.getData("PeoplePerception/Person/{}/ExpressionProperties".format(face_id))
    if not props or len(props) != 5:
        return "neutral"

    emotions = ["neutral", "happy", "surprised", "angry", "sad"]
    thresholds = {
        "neutral": 0.5,
        "happy": 0.35,
        "surprised": 0.4,
        "angry": 0.6,
        "sad": 0.5
    }

    recognized = [(e, val) for e, val in zip(emotions, props) if val > thresholds[e]]
    if not recognized:
        return "neutral"

    dominant_emotion = max(recognized, key=lambda x: x[1])[0]
    return dominant_emotion

print("Storytelling started...")

try:
    while True:
        new_emotion = get_dominant_emotion()

        if new_emotion not in stories:
            new_emotion = "neutral"

        if new_emotion != current_emotion:
            print("Emotion changed from {} to {}, switching story.".format(current_emotion, new_emotion))
            current_emotion = new_emotion
            if current_emotion == "neutral":
                current_story = stories["neutral"]
            else:
                current_story = merge_emotion_story(stories["neutral"], stories[current_emotion])
            sentence_index = 0

        if sentence_index < len(current_story):
            sentence = current_story[sentence_index]
            print("Pepper says: {}".format(sentence))
            speak_with_animation(sentence, current_emotion)

            if listen_for_continue(timeout=20):
                sentence_index += 1
            else:
                print("No user input, ending storytelling.")
                break
        else:
            print("Story finished.")
            break

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    face_detection.unsubscribe("storytelling")
    print("Face detection unsubscribed, storytelling session ended.")