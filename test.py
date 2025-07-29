#!/usr/bin/env python
# -*- coding: utf-8 -*-

from naoqi import ALProxy

# Replace this with your Pepper's IP address
PEPPER_IP = "192.168.0.102"
PORT = 9559

def main():
    try:
        # Stop autonomous life to prevent background movements
        life_proxy = ALProxy("ALAutonomousLife", PEPPER_IP, PORT)
        life_proxy.setState("disabled")  # Other options: "interactive", "solitary", "safeguard"
        print("Autonomous Life disabled.")

        # Say "Hello there"
        tts = ALProxy("ALTextToSpeech", PEPPER_IP, PORT)
        tts.say("Hello")
        print("Pepper said: Hello there")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
