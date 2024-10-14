import cv2
import numpy as np
from serial import Serial

# Initialize serial communication with Arduino
port = 'COM7'  # Update with your port number
serialCom = Serial(port, 9600)

# Open the video capture (use 'fire.mp4' for a video file or 1 for live camera)
camera = cv2.VideoCapture(1)

# Camera settings
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

# Function to map a number from one range to another
def num_to_range(num, inMin, inMax, outMin, outMax):
    return outMin + (int(num - inMin) / int(inMax - inMin) * (outMax - outMin))

# Fire detection function
def detect_fire(frame):
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)

    # Thresholding to identify high-intensity regions
    thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY)[1]

    # Blob detection
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 100
    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(thresh)

    return keypoints

# Main loop
while True:
    ret, frame = camera.read()
    if not ret:
        break

    # Detect fire in the current frame
    fire_keypoints = detect_fire(frame)

    # Draw keypoints and send position commands if fire is detected
    if len(fire_keypoints) > 0:
        # Get the position of the first detected fire region
        x, y = int(fire_keypoints[0].pt[0]), int(fire_keypoints[0].pt[1])

        # Draw a circle around the detected fire region
        cv2.circle(frame, (x, y), 50, (0, 0, 255), 2)

        # Map the detected position to the servo's control range
        servoX = int(num_to_range(x, 0, 720, 150, 50))
        servoY = int(num_to_range(y, 0, 640, 30, 150))

        # Create the command string to send via serial
        cmdSend = f"S1:{servoX}S2:{servoY}."
        print(f"Sending: {cmdSend}")
        
        # Send the command to the serial port
        serialCom.write(cmdSend.encode())

        # Optionally, send an alert to activate the water pump
        pump_cmd = "PUMP:ON"
        serialCom.write(pump_cmd.encode())

    # Display the current frame
    cv2.imshow("Fire Detector", frame)

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
camera.release()
cv2.destroyAllWindows()
serialCom.close()
