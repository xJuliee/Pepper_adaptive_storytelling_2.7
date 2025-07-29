from naoqi import ALProxy
import socket
import time
import struct
import cv2
import numpy as np
import threading

# === Pepper Configuration ===
PEPPER_IP = "192.168.0.102"
PEPPER_PORT = 9559

# === Laptop Streaming Target ===
LAPTOP_IP = "10.9.73.57"
LAPTOP_PORT = 5000        # Laptop's image receiver port
PEPPER_RECEIVE_PORT = 6000  # Port to receive classified emotion back

# === Pepper Camera Setup ===
resolution = 2  # 640x480
color_space = 13  # kBGRColorSpace
fps = 10

camera_name = "pepperStream"
capture_id = None
sock = None

# === Emotion Receiving Function ===
def emotion_receiver():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', PEPPER_RECEIVE_PORT))
    server_socket.listen(5)
    print("[Emotion Receiver] Listening on port", PEPPER_RECEIVE_PORT)

    try:
        while True:
            conn, addr = server_socket.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    emotion = data.decode('utf-8')
                    print("[Emotion Receiver] Received emotion: {emotion}")
    except Exception as e:
        print("[Emotion Receiver] Error:", e)
    finally:
        server_socket.close()

# === Start Emotion Receiver Thread ===
emotion_thread = threading.Thread(target=emotion_receiver, daemon=True)
emotion_thread.start()

# === Start Video Streaming to Laptop ===
try:
    # Disable autonomous behavior
    awareness = ALProxy("ALBasicAwareness", PEPPER_IP, PEPPER_PORT)
    awareness.stopAwareness()

    # Optional: Stop any tracking behavior
    tracker = ALProxy("ALTracker", PEPPER_IP, PEPPER_PORT)
    tracker.stopTracker()

    # Subscribe to camera
    video_proxy = ALProxy("ALVideoDevice", PEPPER_IP, PEPPER_PORT)
    capture_id = video_proxy.subscribeCamera(camera_name, 0, resolution, color_space, fps)

    # Connect to laptop
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((LAPTOP_IP, LAPTOP_PORT))
    print("[Video Sender] Connected to laptop at", LAPTOP_IP, LAPTOP_PORT)

    while True:
        image = video_proxy.getImageRemote(capture_id)
        if image is None:
            print("[Video Sender] No image received")
            time.sleep(0.1)
            continue

        width = image[0]
        height = image[1]
        array = image[6]

        # Convert raw bytes to numpy array
        np_arr = np.frombuffer(array, np.uint8)
        img = np_arr.reshape((height, width, 3))

        # Encode frame as JPEG
        result, jpg = cv2.imencode('.jpg', img)
        if not result:
            print("[Video Sender] Failed to encode frame")
            continue

        jpg_bytes = jpg.tobytes()

        # Send JPEG size header and frame
        sock.sendall(struct.pack(">I", len(jpg_bytes)))
        sock.sendall(jpg_bytes)

        time.sleep(1.0 / fps)

except KeyboardInterrupt:
    print("Interrupted by user, exiting...")
except Exception as e:
    print("[Main] Error:", e)

finally:
    if capture_id:
        try:
            video_proxy.unsubscribe(capture_id)
        except Exception as e:
            print("Warning: could not unsubscribe cleanly:", e)
    if sock:
        sock.close()