# -*- coding: utf-8 -*-

from naoqi import ALProxy
import time

PEPPER_IP = "PEPPER_IP"  # Replace with your Pepper's IP

tts = ALProxy("ALTextToSpeech", PEPPER_IP, 9559)
anim = ALProxy("ALAnimationPlayer", PEPPER_IP, 9559)

stories = {
    "neutral": [
        "Once upon a time, in a cheerful little town filled with sunshine and laughter, lived a very talkative and very helpful character named... The Hand.",
        "“Greetings, Traveller!” the Hand beamed. “Welcome to our lovely little town! It’s cozy, friendly, and completely safe! Well... mostly.”",
        "Just then—ROOOAARRR! A big green dinosaur burst onto the square with a growl, a grumble, and an odd little coo.",
        "The Hand froze. “Uh-oh... That’s new. Maybe if we stay very still, it’ll go away?”",
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
        "Levi bit into it—and began to glow!",
        "Lights burst from his belly, and Levi transformed into a Dragon!",
        "“I have wings!” he shouted surprised.",
        "The baker laughed. “Now you can bake your own bread—no more smashing bakeries!”",
        "Levi nodded. “Thank you, Baker. And thank you, Hand. And you too, Traveller!”",
        "He coughed up a slightly soggy sourdough and handed it to The Hand.",
        "“Oh… uhm… thank you,” said The Hand.",
        "Levi gave one last roar and flew off toward Dino-land.",
        "The Hand turned to the Traveller. “Well, that was... something.”",
        "The Baker stepped in. “You’ve earned a reward. I’ve got fresh bread for you both!”",
        "“And maybe next time,” said The Hand, “we’ll visit a town *without* cake-powered flying dinosaurs.”"
    ]
}

def speak_with_animation(text):
    anim_tag = "animations/Stand/Gestures/Explain_1"
    full_text = "^start({}) {} ^wait({})".format(anim_tag, text, anim_tag)
    task_id = tts.post.say(full_text)  # start speaking asynchronously
    tts.wait(task_id)                   # wait until speech finishes

print("Starting static storytelling...")

try:
    for sentence in stories["neutral"]:
        print("Pepper says: {}".format(sentence))
        speak_with_animation(sentence)

except KeyboardInterrupt:
    print("Storytelling interrupted by user.")