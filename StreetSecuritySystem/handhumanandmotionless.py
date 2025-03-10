import cv2
import mediapipe as mp
import requests
import time
import threading
import numpy as np
from playsound import playsound

# Firebase Database URL (Replace with your actual URL)
database_url = 'https://streetsecuritysystem-default-rtdb.firebaseio.com/'

# Initialize Mediapipe Hand and Pose Tracking
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

alarm_triggered = False  # Flag to track alarm state
motionless_start_time = None  # Track when human stops moving
previous_pose_landmarks = None  # Store previous pose positions

# Play alarm sound in a separate thread
def play_alarm():
    global alarm_triggered
    while alarm_triggered:
        playsound(r'C:\\Users\\mariy\\OneDrive\\Desktop\\Gouri\\StreetSecuritySystem\\alarm.wav')  # Update with your actual alarm file path
        time.sleep(1)

# **Closed Fist Detection Function**
def is_emergency_gesture(landmarks):
    """
    Returns True if the hand is in a closed fist position.
    """
    fingers_closed = (
        landmarks[8].y > landmarks[6].y and  # Index finger tip below knuckle
        landmarks[12].y > landmarks[10].y and  # Middle finger tip below knuckle
        landmarks[16].y > landmarks[14].y and  # Ring finger tip below knuckle
        landmarks[20].y > landmarks[18].y  # Pinky tip below knuckle
    )

    # Thumb should be tucked in (not stretched outward)
    thumb_closed = landmarks[4].x > landmarks[3].x  

    return fingers_closed and thumb_closed  # Return True only when all fingers are closed

# **Update Firebase with Emergency Data**
def update_data(data):
    url = f'{database_url}/emergency.json'  # Store emergency data under "emergency" node
    response = requests.patch(url, json=data)  # Use PATCH to avoid overwriting database
    if response.status_code == 200:
        print("Data updated successfully:", response.json())
    else:
        print("Error updating data:", response.text)

# **Check if Human is Motionless**
def is_motionless(current_landmarks, previous_landmarks, threshold=0.01):
    """
    Detects if the human has remained motionless.
    Compares current and previous key pose points.
    """
    if previous_landmarks is None:
        return False

    movement = []
    for i in range(len(current_landmarks)):
        movement.append(abs(current_landmarks[i] - previous_landmarks[i]))

    avg_movement = np.mean(movement)  # Calculate average movement

    return avg_movement < threshold  # If movement is small, return True

# **Start Human, Gesture & Motion Detection**
def start_detection():
    global alarm_triggered, motionless_start_time, previous_pose_landmarks
    cap = cv2.VideoCapture(0)  # Open webcam
    print("Show the emergency gesture (closed fist) to trigger the alarm...")

    last_gesture_time = time.time()
    gesture_timeout = 2  # Seconds before stopping the alarm if the gesture disappears

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # Mirror the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB for Mediapipe

        # Process both hand and pose detection
        hand_results = hands.process(rgb_frame)
        pose_results = pose.process(rgb_frame)

        gesture_detected = False
        human_detected = False
        human_motionless = False

        # Check if a human is present (Pose detection)
        if pose_results.pose_landmarks:
            human_detected = True
            mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            print("👤 Human Detected!")

            # Convert pose landmarks to a list of (x, y) coordinates
            current_pose_landmarks = [pose_results.pose_landmarks.landmark[i].x for i in range(33)]

            # Check if motionless
            if is_motionless(current_pose_landmarks, previous_pose_landmarks):
                if motionless_start_time is None:
                    motionless_start_time = time.time()  # Start timer

                elif time.time() - motionless_start_time > 5:  # Check if 5 sec passed
                    human_motionless = True
                    print("🚶‍♂️ Human Detected Motionless!")
            else:
                motionless_start_time = None  # Reset timer if movement detected

            previous_pose_landmarks = current_pose_landmarks  # Update previous pose

        # Check if emergency gesture (closed fist) is detected
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                if is_emergency_gesture(hand_landmarks.landmark):
                    gesture_detected = True
                    last_gesture_time = time.time()

                    if not alarm_triggered:
                        print("🚨 Emergency Gesture Detected! Triggering Alarm...")
                        alarm_triggered = True
                        update_data({'D1': '1', 'D2': '0', 'SMC': '50', 'msg': '11a10'})
                        threading.Thread(target=play_alarm, daemon=True).start()

        # If the gesture is no longer detected, stop the alarm
        if not gesture_detected and alarm_triggered:
            if time.time() - last_gesture_time > gesture_timeout:
                print("🛑 Gesture removed. Stopping Alarm...")
                alarm_triggered = False
                update_data({'D1': '1', 'D2': '0', 'SMC': '50', 'msg': '10a200'})

        cv2.imshow("Human, Gesture & Motion Detection", frame)  # Show webcam feed
        if cv2.waitKey(10) & 0xFF == ord('q'):  # Press 'q' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

# **Run the Detection System**
input("Press Enter to start detection...")
start_detection()
