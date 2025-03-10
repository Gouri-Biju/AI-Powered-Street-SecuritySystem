import cv2
import mediapipe as mp
import requests
import time
import threading
import numpy as np
from playsound import playsound
from datetime import datetime

# Firebase Realtime Database URL
DATABASE_URL = 'https://streetsecuritysystem-default-rtdb.firebaseio.com/'

# Initialize Mediapipe Hand and Pose Tracking
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

alarm_triggered = False  # Flag for alarm state
motionless_start_time = None  # Track motionless human time
previous_pose_landmarks = None  # Store previous pose positions

def play_alarm():
    global alarm_triggered
    while alarm_triggered:
        playsound(r'C:\\Users\\mariy\\OneDrive\\Desktop\\Gouri\\StreetSecuritySystem\\alarm.wav')
        time.sleep(1)

# Function to log events to Firebase
def log_event(event_type, location, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event_data = {
        "timestamp": timestamp,
        "location": location,
        "event_type": event_type,
        "details": details
    }
    url = f"{DATABASE_URL}/events.json"
    response = requests.post(url, json=event_data)
    if response.status_code == 200:
        print("✅ Event logged successfully:", response.json())
    else:
        print("❌ Error logging event:", response.text)

def is_emergency_gesture(landmarks):
    fingers_closed = (
        landmarks[8].y > landmarks[6].y and
        landmarks[12].y > landmarks[10].y and
        landmarks[16].y > landmarks[14].y and
        landmarks[20].y > landmarks[18].y
    )
    thumb_closed = landmarks[4].x > landmarks[3].x  
    return fingers_closed and thumb_closed

def is_motionless(current_landmarks, previous_landmarks, threshold=0.01):
    if previous_landmarks is None:
        return False
    movement = [abs(current_landmarks[i] - previous_landmarks[i]) for i in range(len(current_landmarks))]
    return np.mean(movement) < threshold

def start_detection():
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

        if pose_results.pose_landmarks:
            human_detected = True
            mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            current_pose_landmarks = [pose_results.pose_landmarks.landmark[i].x for i in range(33)]

            if is_motionless(current_pose_landmarks, previous_pose_landmarks):
                if motionless_start_time is None:
                    motionless_start_time = time.time()
                elif time.time() - motionless_start_time > 5:
                    human_motionless = True
                    log_event("Motionless Human", "Unknown", "Person remained motionless for 5 seconds")
            else:
                motionless_start_time = None

            previous_pose_landmarks = current_pose_landmarks

        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                if is_emergency_gesture(hand_landmarks.landmark):
                    gesture_detected = True
                    last_gesture_time = time.time()
                    if not alarm_triggered:
                        print("🚨 Emergency Gesture Detected! Triggering Alarm...")
                        alarm_triggered = True
                        log_event("Emergency Gesture", "Unknown", "Closed fist detected")
                        threading.Thread(target=play_alarm, daemon=True).start()
        
        if not gesture_detected and alarm_triggered:
            if time.time() - last_gesture_time > gesture_timeout:
                print("🛑 Gesture removed. Stopping Alarm...")
                alarm_triggered = False
                log_event("Alarm Stopped", "Unknown", "Emergency gesture disappeared")

        cv2.imshow("Security System", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

input("Press Enter to start detection...")
start_detection()