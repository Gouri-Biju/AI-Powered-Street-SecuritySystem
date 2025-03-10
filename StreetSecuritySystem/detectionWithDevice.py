import cv2
import mediapipe as mp
import requests
import time
import threading
import numpy as np
from playsound import playsound
from datetime import datetime

# ✅ Firebase Realtime Database URL
DATABASE_URL = 'https://streetsecuritysystem-default-rtdb.firebaseio.com/'

# ✅ Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ✅ Global Variables
alarm_triggered = False  
motionless_start_time = None
previous_pose_landmarks = None


def play_alarm():
    """Plays the alarm sound in a loop while alarm is triggered."""
    global alarm_triggered
    while alarm_triggered:
        playsound(r'C:\\Users\\mariy\\OneDrive\\Desktop\\Gouri\\StreetSecuritySystem\\alarm.wav')
        time.sleep(1)


def log_event(event_type, details):
    """Logs detected events (Emergency Gesture & Motionless Person) to Firebase."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    location = "Kalamassery"
    event_data = {
        "timestamp": timestamp,
        "event_type": event_type,
        "details": details,
        "location":location
    }
    url = f"{DATABASE_URL}/events.json"
    response = requests.post(url, json=event_data)
    if response.status_code == 200:
        print("✅ Event logged successfully:", response.json())
    else:
        print("❌ Error logging event:", response.text)


def update_database(d1, d2, smc, msg):
    """Updates Firebase Realtime Database with the given values."""
    data_to_update = {
        "D1": d1,
        "D2": d2,
        "SMC": smc,
        "msg": msg
    }
    response = requests.patch(f"{DATABASE_URL}/.json", json=data_to_update)
    if response.status_code == 200:
        print("✅ Firebase updated:", response.json())
    else:
        print("❌ Error updating Firebase:", response.text)


def is_emergency_gesture(landmarks):
    """Checks if the detected hand is making an emergency gesture (closed fist)."""
    fingers_closed = (
        landmarks[8].y > landmarks[6].y and
        landmarks[12].y > landmarks[10].y and
        landmarks[16].y > landmarks[14].y and
        landmarks[20].y > landmarks[18].y
    )
    thumb_closed = landmarks[4].x > landmarks[3].x  
    return fingers_closed and thumb_closed


def is_motionless(current_landmarks, previous_landmarks, threshold=0.01):
    """Determines if a human has remained motionless for too long."""
    if previous_landmarks is None:
        return False
    movement = [abs(current_landmarks[i] - previous_landmarks[i]) for i in range(len(current_landmarks))]
    return np.mean(movement) < threshold


def start_detection():
    """Starts real-time security system detection using OpenCV and MediaPipe."""
    global alarm_triggered, motionless_start_time, previous_pose_landmarks
    cap = cv2.VideoCapture(0)
    last_gesture_time = time.time()
    gesture_timeout = 2

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_results = hands.process(rgb_frame)
        pose_results = pose.process(rgb_frame)

        gesture_detected = False
        human_detected = False
        human_motionless = False

        # ✅ Detect Human Presence
        if pose_results.pose_landmarks:
            human_detected = True
            mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            current_pose_landmarks = [pose_results.pose_landmarks.landmark[i].x for i in range(33)]

            # ✅ Check for Motionless Human
            if is_motionless(current_pose_landmarks, previous_pose_landmarks):
                if motionless_start_time is None:
                    motionless_start_time = time.time()
                elif time.time() - motionless_start_time > 5:
                    human_motionless = True
                    print("⚠️ Motionless Person Detected!")
                    log_event("Motionless Person Detected", "Person remained motionless for 5 seconds")
                    update_database("1", "0", "50", "11a200")  # 🔄 Emergency State Update
            else:
                motionless_start_time = None

            previous_pose_landmarks = current_pose_landmarks

        # ✅ Detect Emergency Gesture
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                if is_emergency_gesture(hand_landmarks.landmark):
                    gesture_detected = True
                    last_gesture_time = time.time()
                    if not alarm_triggered:
                        print("🚨 Emergency Gesture Detected! Triggering Alarm...")
                        alarm_triggered = True
                        log_event("Emergency Alert Detected", "Closed fist detected")
                        update_database("1", "0", "50", "11a200")  # 🔄 Emergency State Update
                        threading.Thread(target=play_alarm, daemon=True).start()
                        
        
        # ✅ Update Firebase on Human Detection (No Emergency)
        if human_detected and not human_motionless and not gesture_detected:
            update_database("1", "0", "50", "11a200") #normal te Update
            print("human detected")
        elif not human_detected:
             update_database("1", "0", "50", "11a10")

        # ✅ Display Video Feed
        cv2.imshow("Security System", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ✅ Start Detection
input("Press Enter to start detection...")
start_detection()
