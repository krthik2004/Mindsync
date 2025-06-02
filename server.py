from flask import Flask, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
from PIL import Image
import io
import base64
import re
from flask_cors import CORS
import random
import os
import logging
from dotenv import load_dotenv
import tensorflow as tf
from google import genai
import google.generativeai as genai

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

genai.configure(api_key="AIzaSyAOvB9n5s849bV-2_XuZsTvdf-dcpjF6dE")
client = genai

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.flaskenv')
load_dotenv(dotenv_path)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.join(BASE_DIR, 'ml')
ML_DIR1 = os.path.join(ML_DIR, 'ml')
MODEL_DIR = os.path.join(ML_DIR1, 'model')
HAAR_CASCADE_PATH = os.path.join(ML_DIR, 'haarcascades', 'haarcascade_frontalface_default.xml')

# Load emotion detection model
emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}

def load_emotion_model():
    try:
        logger.info(f"Loading emotion model from {MODEL_DIR}")
        model_path = os.path.join(MODEL_DIR, 'emotion_model.h5')
        
        # Enable mixed precision
        tf.keras.mixed_precision.set_global_policy('mixed_float16')
        
        # Load the model with TensorFlow's load_model
        model = tf.keras.models.load_model(model_path, compile=False)
        
        # Compile the model
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("Emotion model loaded successfully!")
        return model
    except Exception as e:
        logger.error(f"Error loading emotion model: {str(e)}")
        return None

# Initialize models
try:
    emotion_model = load_emotion_model()
    face_detector = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    if face_detector.empty():
        raise Exception("Error loading face detector cascade")
    logger.info("Successfully initialized all models")
except Exception as e:
    logger.error(f"Failed to initialize models: {str(e)}")
    raise

# Conversation memory to maintain context
conversation_memory = {}
user_preferences = {}  # Store user preferences for features

def get_music_suggestions(emotion):
    """Get music suggestions based on emotion."""
    music_prompts = {
        "Angry": "Suggest 3 calming songs that might help someone who is feeling angry.",
        "Sad": "Recommend 3 uplifting songs that could help someone who is feeling sad.",
        "Happy": "Suggest 3 energetic, feel-good songs to match someone's happy mood.",
        "Fearful": "Recommend 3 comforting songs that might help someone who is feeling anxious or fearful.",
        "Disgusted": "Suggest 3 pleasant, positive songs to help shift someone's mood from disgust.",
        "Surprised": "Recommend 3 interesting songs that match an excited, surprised mood.",
        "Neutral": "Suggest 3 balanced, melodic songs that maintain a calm, neutral mood."
    }
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(music_prompts.get(emotion, music_prompts["Neutral"]))
        return response.text
    except Exception as e:
        logger.error(f"Error getting music suggestions: {str(e)}")
        return "I'm having trouble suggesting music right now. Please try again later."

def process_commands(message, session_id):
    """Process special commands in the chat."""
    commands = {
        "/start_emotion": "Started emotion detection.",
        "/stop_emotion": "Stopped emotion detection.",
        "/music": "Here are some music suggestions based on your current emotion:",
        "/help": "Available commands:\n/start_emotion - Start emotion detection\n/stop_emotion - Stop emotion detection\n/music - Get music suggestions\n/help - Show this help message"
    }
    
    message_lower = message.lower().strip()
    logger.debug(f"Processing command: {message_lower} for session {session_id}")
    
    if message_lower in commands:
        if session_id not in user_preferences:
            user_preferences[session_id] = {"emotion_detection": False}
            
        if message_lower == "/start_emotion":
            user_preferences[session_id]["emotion_detection"] = True
            logger.info(f"Emotion detection enabled for session {session_id}")
        elif message_lower == "/stop_emotion":
            user_preferences[session_id]["emotion_detection"] = False
            logger.info(f"Emotion detection disabled for session {session_id}")
        elif message_lower == "/music":
            current_emotion = user_preferences.get(session_id, {}).get("current_emotion", "Neutral")
            return commands["/music"] + "\n\n" + get_music_suggestions(current_emotion)
            
        return commands[message_lower]
    return None

def get_ai_response(message, emotion, session_id):
    try:
        if session_id not in conversation_memory:
            conversation_memory[session_id] = []

        # Check for commands first
        command_response = process_commands(message, session_id)
        if command_response:
            return command_response

        # Update current emotion for the session
        if session_id not in user_preferences:
            user_preferences[session_id] = {"emotion_detection": False}
        user_preferences[session_id]["current_emotion"] = emotion

        # Add first-time context into the user message
        if not conversation_memory[session_id]:
            context_message = (
                f"You are a creative and empathetic AI counselor. The user is feeling {emotion}. "
                f"Respond in a friendly, supportive way, like talking to a friend. Keep it concise, "
                f"but also add some warmth, creativity, and empathy in your responses. Make the user feel heard."
            )
            conversation_memory[session_id].append({"role": "user", "parts": [context_message]})
        else:
            conversation_memory[session_id].append({"role": "user", "parts": [message]})

        # Create the chat model and session
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat(history=conversation_memory[session_id][-5:])

        # Send message and get reply
        response = chat.send_message(message)

        # Save AI response
        conversation_memory[session_id].append({"role": "model", "parts": [response.text]})

        return response.text

    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        return get_fallback_response(emotion)

def get_fallback_response(emotion):
    """Provide fallback responses when AI is unavailable."""
    emotion_context = conversation_context.get(emotion, conversation_context["Neutral"])
    return random.choice(emotion_context["greetings"])

# Keep the existing conversation_context dictionary for fallback responses
conversation_context = {
    "Angry": {
        "greetings": [
            "I notice you seem frustrated. Would you like to talk about what's bothering you?",
            "It's okay to feel angry. I'm here to listen if you want to share.",
            "Sometimes talking about what makes us angry can help. What's on your mind?",
            "I can see this is important to you. Would you like to discuss it?"
        ]
    },
    "Surprised": {
        "greetings": [
            "That sounds surprising! What happened?",
            "Wow! That must have caught you off guard. Want to share more?",
            "Surprises can be exciting or shocking. How are you feeling about it?",
            "Unexpected things happen all the time. How do you feel about this one?"
        ]
    },
    "Sad": {
        "greetings": [
            "I'm sorry you're feeling down. Want to talk about it?",
            "Feeling sad is okay. I'm here for you.",
            "If you need someone to listen, I'm right here.",
            "Sadness can be heavy, but you're not alone. Want to share?"
        ]
    },
    "Neutral": {
        "greetings": [
            "Hey there! How's your day going?",
            "I'm here to chat! What's on your mind?",
            "You seem calm today. Anything you'd like to talk about?",
            "I'm always here to listen. What's up?"
        ]
    },
    "Happy": {
        "greetings": [
            "That's awesome! What's making you happy today?",
            "I'm glad to hear that! Want to share your good news?",
            "Happiness is contagious! Tell me more!",
            "That's great! I'd love to hear more about it."
        ]
    },
    "Fearful": {
        "greetings": [
            "That sounds scary. Want to talk about what's making you feel this way?",
            "Fear is a natural emotion. I'm here to listen.",
            "You're not alone in this. Want to share what's worrying you?",
            "It's okay to feel afraid. I'm here to support you."
        ]
    },
    "Disgusted": {
        "greetings": [
            "That sounds unpleasant. What happened?",
            "Feeling disgusted can be strong. Want to talk about it?",
            "Something must have really put you off. Want to share?",
            "I hear you. What's making you feel this way?"
        ]
    }
}

def process_frame(frame_data):
    """Process a frame to detect emotion."""
    try:
        logger.debug("Processing new frame...")
        # Convert base64 image to numpy array
        image_data = re.sub('^data:image/.+;base64,', '', frame_data)
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_detector.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)
        
        if len(faces) > 0:
            logger.debug(f"Found {len(faces)} faces in frame")
            (x, y, w, h) = faces[0]  # Process the first face only
            roi_gray_frame = gray_frame[y:y + h, x:x + w]
            cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray_frame, (48, 48)), -1), 0)
            
            # Predict emotion
            emotion_prediction = emotion_model.predict(cropped_img)
            maxindex = int(np.argmax(emotion_prediction))
            detected_emotion = emotion_dict[maxindex]
            logger.debug(f"Detected emotion: {detected_emotion}")
            
            return detected_emotion
        else:
            logger.debug("No faces detected in frame")
        
        return None
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        return None

@socketio.on('process_frame')
def handle_frame(data):
    """Handle incoming frame data for emotion detection."""
    try:
        session_id = request.sid
        logger.debug(f"Processing frame for session {session_id}")
        
        if not user_preferences.get(session_id, {}).get("emotion_detection", False):
            logger.debug(f"Emotion detection disabled for session {session_id}")
            return

        image_data = data['image']
        emotion = process_frame(image_data)
        if emotion:
            logger.info(f"Emitting emotion {emotion} for session {session_id}")
            user_preferences[session_id]["current_emotion"] = emotion
            emit('emotion_detected', {'emotion': emotion})
        else:
            logger.debug("No emotion detected")
    except Exception as e:
        logger.error(f"Error in handle_frame: {str(e)}")
        emit('error', {'message': 'Error processing frame'})

@socketio.on('chat_message')
def handle_message(data):
    """Handle incoming chat messages."""
    try:
        message = data['message']
        session_id = request.sid
        logger.debug(f"Received chat message from session {session_id}: {message}")
        
        emotion = user_preferences.get(session_id, {}).get("current_emotion", "Neutral")
        logger.debug(f"Current emotion for session {session_id}: {emotion}")
        
        # Get AI response
        response = get_ai_response(message, emotion, session_id)
        logger.debug(f"Sending response to session {session_id}: {response}")
        emit('chat_response', {'message': response})
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        emit('error', {'message': 'Error processing message'})

if __name__ == '__main__':
    try:
        logger.info("Starting Flask-SocketIO server...")
        socketio.run(app, host='127.0.0.1', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")