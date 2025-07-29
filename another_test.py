from naoqi import ALProxy
import time
import socket

# === Configuration ===
ROBOT_IP = "192.168.0.102"
PORT = 9559
VIDEO_RESOLUTION = 2  # 640x480
VIDEO_COLOR_SPACE = 11  # RGB
VIDEO_FPS = 10
SUBSCRIPTION_NAME = "emotionStream"

# === Connect to proxies ===
def connect_proxy(name):
    try:
        print("[DEBUG] Connecting to {}...".format(name))
        proxy = ALProxy(name, ROBOT_IP, PORT)
        print("[INFO] Connected to {}.".format(name))
        return proxy
    except Exception as e:
        print("[ERROR] Failed to connect to {}: {}".format(name, e))
        raise

# === Emotion classification simulation ===
def classify_emotion(image_data):
    print("[DEBUG] Simulating emotion classification...")
    return "happy"  # Replace with real classifier if needed

# === Main ===
def main():
    # Step 1: Connect to ALVideoDevice and ALTextToSpeech
    try:
        video_proxy = connect_proxy("ALVideoDevice")
        tts_proxy = connect_proxy("ALTextToSpeech")
    except Exception:
        print("[FATAL] Could not connect to essential proxies. Exiting.")
        return

    # Step 2: Subscribe to video stream
    try:
        print("[DEBUG] Subscribing to video stream...")
        video_proxy.unsubscribeAllInstances(SUBSCRIPTION_NAME)
        capture_id = video_proxy.subscribeCamera(SUBSCRIPTION_NAME, 0, VIDEO_RESOLUTION, VIDEO_COLOR_SPACE, VIDEO_FPS)
        print("[INFO] Video stream subscribed with ID: {}".format(capture_id))
    except Exception as e:
        print("[ERROR] Failed to subscribe to video stream: {}".format(e))
        return

    try:
        while True:
            # Step 3: Get image
            print("[DEBUG] Calling getImageRemote...")
            try:
                image = video_proxy.getImageRemote(capture_id)
                print("[INFO] Image captured successfully.")
            except Exception as e:
                print("[ERROR] Failed to get image: {}".format(e))
                break  # Stop loop on stream failure

            # Step 4: Classify emotion
            try:
                emotion = classify_emotion(image)
                print("[INFO] Emotion classified as: {}".format(emotion))
            except Exception as e:
                print("[ERROR] Emotion classification failed: {}".format(e))
                continue  # Skip speaking

            time.sleep(1)  # Pause between loops

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")

    # Step 6: Clean up
    try:
        print("[DEBUG] Unsubscribing from video stream...")
        video_proxy.unsubscribe(capture_id)
        print("[INFO] Video stream unsubscribed.")
    except Exception as e:
        print("[WARN] Could not unsubscribe cleanly: {}".format(e))

    print("[INFO] Script ended.")

if __name__ == "__main__":
    main()
