from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import boto3
import cv2
import pyaudio
import wave
import random
import os
from datetime import datetime
import numpy as np

app = Flask(__name__)
CORS(app)

# AWS S3 setup
s3 = boto3.client('s3')
BUCKET_NAME = 'virtualinterviewstorage'

# Directory to store videos and audios locally
LOCAL_STORAGE_DIR = 'local_storage'
os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

# Load questions from text file or list
questions = [
    "Tell Us something about Yourself?",
    "Why are you interested in this internship, and how does it align with your career goals?",
    "What specific skills or knowledge do you hope to gain from this internship?",
    "Can you provide an example of a time when you had to work as part of a team? What was your approach to collaboration, and how did you handle any conflicts or challenges?",
    "Can you describe a project or task from your previous experience (or academic work) that you are particularly proud of? What was your role, and what did you learn from it?",
    "Describe a situation where you had to quickly learn something new or adapt to a change. How did you handle it, and what was the outcome?",
    "What motivated you to apply for this internship, and what interests you about our company or the role?",
    "What skills or strengths do you believe you bring to this internship, and how do you think they will help you succeed?",
    "How do you handle challenges or setbacks, especially when you’re working on something unfamiliar or difficult?",
    "Can you tell us about your educational background and any relevant coursework or projects you have completed?",
    "What are your strengths and weaknesses, and how do you plan to address your weaknesses during this internship?",
    "How do you handle feedback and criticism, and can you give an example of how you have used feedback to improve your work?",
    "How would you approach a project or task if you were unfamiliar with the topic or required specific knowledge?",
    "What tools or software are you familiar with that are relevant to this internship role?",
    "What are your long-term career goals, and how does this internship help you achieve them?",
    "Can you give an example of a situation where you had to communicate complex information to someone with less expertise?",
    "How would you handle a situation where you were given unclear instructions or expectations for a task?",
    "What extracurricular activities or volunteer experiences have you been involved in, and how do they relate to this internship?",
    "How do you plan to balance this internship with any other commitments you may have?"
]

# Route to start the interview
@app.route('/start-interview', methods=['GET'])
def start_interview():
    return render_template('index.html')

# Route to check mic and camera
@app.route('/check-devices', methods=['POST', 'GET'])
def check_devices():
    mic_working = check_mic()
    camera_working = check_camera()
    if not mic_working or not camera_working:
        return jsonify({
            'status': 'error',
            'mic': mic_working,
            'camera': camera_working
        }), 400
    return jsonify({'status': 'success'}), 200

# Route to conduct interview
@app.route('/conduct-interview', methods=['POST'])
def conduct_interview():
    selected_questions = random.sample(questions, 6)
    return jsonify({'questions': selected_questions})

# Route to save video
@app.route('/save-video', methods=['POST'])
def save_video():
    video_data = request.files['video']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"interview_{timestamp}.mp4"
    local_video_path = os.path.join(LOCAL_STORAGE_DIR, video_filename)
    
    # Save video locally
    video_data.save(local_video_path)
    
    # Upload video to S3
    s3.upload_file(local_video_path, BUCKET_NAME, video_filename)
    
    # Remove local video file after upload
    os.remove(local_video_path)
    
    return jsonify({'status': 'success'}), 200

# Route to save audio
@app.route('/save-audio', methods=['POST'])
def save_audio():
    audio_data = request.files['audio']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"interview_{timestamp}.wav"
    local_audio_path = os.path.join(LOCAL_STORAGE_DIR, audio_filename)
    
    # Save audio locally
    audio_data.save(local_audio_path)
    
    # Upload audio to S3
    s3.upload_file(local_audio_path, BUCKET_NAME, audio_filename)
    
    # Remove local audio file after upload
    os.remove(local_audio_path)
    
    return jsonify({'status': 'success'}), 200

def check_mic():
    # Parameters for audio recording
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 3

    # Initialize pyaudio
    p = pyaudio.PyAudio()

    # Open the audio stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    # Record audio
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Convert recorded frames to numpy array
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)

    # Check if there is any sound in the recorded audio
    if np.abs(audio_data).mean() > 0:
        return True
    else:
        return False

def check_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False
    ret, frame = cap.read()
    cap.release()
    return ret

if __name__ == '__main__':
    app.run(debug=True)
