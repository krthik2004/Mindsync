# 💡 MindSync – Mental Health Tracker

**MindSync** is an intelligent mental health tracking platform that combines AI-based emotion detection with mood tracking, music recommendations, and supportive tools to promote emotional well-being.

---
![image](https://github.com/user-attachments/assets/3a608f96-fd42-4143-9105-5716d7cd07c7)

## 📌 Features

- 🎭 **Emotion Detection** – Detects user emotion using facial expressions powered by deep learning.
- 🎵 **Music Recommendation** – Suggests mood-based songs to uplift or complement the user's current state.
- 📊 **Mood Tracker** – Tracks emotional trends over time.
- 💬 **Therapy Chatbot** – Basic conversational support for stress and anxiety.
- 🚨 **Crisis Resources** – Displays helplines and emergency contacts.

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, Bootstrap, JavaScript / React (if applicable)
- **Backend**: Python
- **AI/ML**: Keras, TensorFlow, OpenCV (for facial emotion recognition)
- **Dataset**: [FER2013 - Facial Expression Recognition Dataset](https://www.kaggle.com/msambare/fer2013)

---


## 📦 Installation

### 1. Clone the Repository

git clone https://github.com/krthik2004/MindSync.git

cd MindSync

2. Install Required Packages

pip install numpy
pip install opencv-python
pip install keras
pip3 install --upgrade tensorflow
pip install pillow



3. Download Dataset
   

Download the FER2013 dataset from Kaggle:



🔗 FER2013 Dataset – Kaggle

Unzip the dataset.

Place the dataset CSV file inside a data/ folder in your project directory:

MindSync/
├── data/
│   └── fer2013.csv

Train the Emotion Detection Model
python TrainEmotionDetector.py


On an Intel i7 with 16 GB RAM, it typically takes around 4 hours.

After training, two files will be generated:

emotion_model.json – model architecture

emotion_model.h5 – model weights

Create a folder named model/ in your project directory and place both files there:

MindSync/
├── model/
│   ├── emotion_model.json
│   └── emotion_model.h5


Test Emotion Detection
After training is complete and model files are in place, test the emotion detector using:

python TestEmotionDetector.py

This will activate your webcam and detect real-time emotions from facial expressions.




📄 Project Structure

MindSync/
├── data/
│   └── fer2013.csv
├── model/
│   ├── emotion_model.json
│   └── emotion_model.h5
├── TrainEmotionDetector.py
├── TestEmotionDetector.py
├── README.md
└── (Additional frontend or backend files)





