# Filename: pepper_client.py (Python 2.7)
import socket
import naoqi
from naoqi import ALProxy
import numpy as np
import cv2
import time
import struct
import pickle

PEPPER_IP = "192.168.1.100"  # Replace with Pepper's IP
PEPPER_PORT = 9559
SERVER_IP = "192.168.1.101"  # Replace with your PC's IP
SERVER_PORT = 9999

# Connect to Pepper modules
video_proxy = ALProxy("ALVideoDevice", PEPPER_IP, PEPPER_PORT)
mem_proxy = ALProxy("ALMemory", PEPPER_IP, PEPPER_PORT)

resolution = 2  # 640x480
color_space = 11  # RGB

# Subscribe to camera
capture_name = "EmotionFeed"
video_proxy.unsubscribeAll()
capture_id = video_proxy.subscribeCamera(capture_name, 0, resolution, color_space, 30)

# Connect to emotion server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))

try:
    while True:
        # Capture frame
        nao_image = video_proxy.getImageRemote(capture_id)

        width = nao_image[0]
        height = nao_image[1]
        array = nao_image[6]

        frame = np.frombuffer(array, dtype=np.uint8).reshape((height, width, 3))
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Serialize image
        data = pickle.dumps(bgr_frame)
        size = struct.pack("L", len(data))  # For Python 3.10+, use "Q" instead of "L"

        # Send to PC
        client_socket.sendall(size + data)

        # Receive emotion label
        label = client_socket.recv(1024)
        print("Received Emotion:", label)

        # Update ALMemory (for your adaptive storytelling)
        mem_proxy.insertData("DetectedEmotion", label)

        time.sleep(0.1)

except Exception as e:
    print("[ERROR]", e)
finally:
    video_proxy.unsubscribe(capture_id)
    client_socket.close()
