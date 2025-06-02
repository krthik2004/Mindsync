import React, { useEffect, useState, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';
import { Camera, MessageSquare, Brain, Activity, ChevronRight } from 'lucide-react';
import Webcam from 'react-webcam';


const socket = io('http://localhost:5000');

// Debug logging for socket events
socket.on('connect', () => console.log('Socket connected'));
socket.on('disconnect', () => console.log('Socket disconnected'));
socket.on('error', (error) => console.error('Socket error:', error));

function App() {
  const [activeTab, setActiveTab] = useState<'emotion' | 'chat'>('emotion');
  const [isDetecting, setIsDetecting] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState<string>('');
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([
    { text: 'Hello! How are you feeling today?', isUser: false }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const webcamRef = useRef<Webcam | null>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    socket.on('emotion_detected', (data: { emotion: string }) => {
      console.log('Emotion detected:', data);
      setCurrentEmotion(data.emotion);
    });

    socket.on('chat_response', (data: { message: string }) => {
      console.log('Chat response received:', data);
      setMessages(prev => [...prev, { text: data.message, isUser: false }]);
    });

    return () => {
      socket.off('emotion_detected');
      socket.off('chat_response');
    };
  }, []);

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        console.log('Capturing and sending frame...');
        socket.emit('process_frame', { image: imageSrc });
      } else {
        console.warn('Failed to capture webcam image');
      }
    }
  }, [webcamRef]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isDetecting) {
      console.log('Starting emotion detection...');
      interval = setInterval(capture, 1000);
      socket.emit('chat_message', { message: '/start_emotion' });
    } else {
      console.log('Stopping emotion detection...');
      socket.emit('chat_message', { message: '/stop_emotion' });
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isDetecting, capture]);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      console.log('Sending chat message:', inputMessage);
      const newMessage = { text: inputMessage, isUser: true };
      setMessages(prev => [...prev, newMessage]);
      socket.emit('chat_message', { 
        message: inputMessage,
        emotion: currentEmotion 
      });
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 to-purple-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Brain className="h-8 w-8 text-indigo-600" />
              <h1 className="text-2xl font-bold text-gray-900">MindSync</h1>
            </div>
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveTab('emotion')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'emotion'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Emotion Detection
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'chat'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Chat Assistant
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {activeTab === 'emotion' ? (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">Emotion Detection</h2>
              <p className="mt-2 text-lg text-gray-600">
                Real-time emotion analysis using advanced AI technology
              </p>
            </div>

            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                {isDetecting ? (
                  <Webcam
                    ref={webcamRef}
                    audio={false}
                    screenshotFormat="image/jpeg"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Camera className="h-16 w-16 text-gray-400" />
                    <p className="ml-4 text-gray-500">Click Start Detection to begin</p>
                  </div>
                )}
              </div>
              <div className="mt-6 space-y-4">
                <button
                  onClick={() => setIsDetecting(!isDetecting)}
                  className={`w-full px-4 py-2 rounded-lg transition-colors ${
                    isDetecting 
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                  }`}
                >
                  {isDetecting ? 'Stop Detection' : 'Start Detection'}
                </button>
                {isDetecting && (
                  <div className="text-center p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-100">
                    <p className="text-lg font-semibold text-indigo-700">
                      Detected Emotion: {currentEmotion || 'Analyzing...'}
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {['Accuracy', 'Real-time Analysis', 'Multiple Emotions'].map((feature) => (
                <div key={feature} className="bg-white rounded-xl p-6 shadow-md">
                  <Activity className="h-8 w-8 text-indigo-600" />
                  <h3 className="mt-4 text-lg font-semibold text-gray-900">{feature}</h3>
                  <p className="mt-2 text-gray-600">Advanced AI-powered emotion detection with high accuracy</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">Chat Assistant</h2>
              <p className="mt-2 text-lg text-gray-600">
                Get personalized assistance based on your emotional state
              </p>
            </div>

            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="h-96 bg-gray-50 rounded-lg p-4 overflow-y-auto mb-4">
                <div className="flex flex-col space-y-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex items-start ${
                        message.isUser ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`rounded-lg p-3 max-w-md ${
                          message.isUser
                            ? 'bg-indigo-600 text-white'
                            : 'bg-indigo-100 text-gray-800'
                        }`}
                      >
                        <p>{message.text}</p>
                      </div>
                    </div>
                  ))}
                  <div ref={messageEndRef} />
                </div>
              </div>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 rounded-lg border-gray-300 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <button
                  onClick={handleSendMessage}
                  className="bg-indigo-600 text-white p-2 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  <ChevronRight className="h-6 w-6" />
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Brain className="h-6 w-6 text-indigo-600" />
              <span className="text-gray-600">© 2025 MindSync. All rights reserved.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;