import React, { useState, useEffect, useRef } from 'react';
import Message from './component/Message';
import { Link } from "react-router-dom";
import { GoGraph } from "react-icons/go";
import Test from './component/Test';
import { sendPrompt } from './api';
import { useUser } from './auth';

function App() {

  const { isSignedIn, user } = useUser();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const chatBoxRef = useRef(null);

  const firstName = user?.firstName || 'there';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const { data } = await sendPrompt(input, sessionId);
      setSessionId(data.session_id);
      const botMessage = { text: data.response, sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        { text: `Sorry ${firstName}, I couldn't process your request.`, sender: 'bot' },
      ]);
    }

    setIsLoading(false);
  };

  // Scroll to the bottom of the chat when new messages are added
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleHistory = () => {
    setShowHistory(!showHistory);
  };

  const scrollToMessage = (index) => {
    const messageElement = document.getElementById(`message-${index}`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const downloadFile = (text) => {
    const blob = new Blob([text], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'bot_response.txt';
    link.click();
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-200">
      {/* History Box */}
      {showHistory && (
        <div className="w-1/4 bg-gray-800 text-gray-300 shadow-inner p-4 space-y-2 overflow-y-auto">
          <h2 className="text-lg font-semibold text-blue-500">History</h2>
          {messages.filter(message => message.sender === 'user').map((message, index) => (
            <div
              key={index}
              className={`p-2 rounded-lg cursor-pointer bg-stone-900`}
              title={message.text}
              onClick={() => scrollToMessage(index)}
            >
              <p className="truncate">{message.text}</p>
            </div>
          ))}
        </div>
      )}

      {/* Main Chat Interface */}
      <div className="flex flex-col flex-grow">
        {/* Header */}
        <div className="bg-slate-950 text-5xl font-bold text-blue-500 neon-text py-6 cursor-pointer">
          <div className="flex ml-4">
            <h1 onClick={toggleHistory}>ManobalAI</h1>
            <div className='ml-4 hover:mr-2 hover:mt-2 active:size-9'>
              <Link to={'\Graph'}>
                <GoGraph size={50} className="border-2 text-cyan-700 rounded-md p-1 border-cyan-400 cursor-pointer bg-teal-300" />
                <p className='text-sm flex text-cyan-700'>View_Graph</p>
              </Link>
            </div>
          </div>
          <Test />
        </div>

        {/* Chat Box */}
        <div
          className="chat-box flex-grow overflow-y-auto p-4 space-y-4 bg-gray-600 shadow-inner rounded-lg neon-border"
          ref={chatBoxRef}
        >
          {messages.map((message, index) => (
            <div key={index} id={`message-${index}`} className={`message flex flex-col ${message.sender === 'user' ? 'items-end' : 'items-start'}`}>
              {message.sender === 'user' && (
                <p className="text-sm text-gray-400 mb-1">{firstName}</p>
              )}
              {message.sender === 'bot' && (
                <p className="text-sm text-gray-400 mb-1">ManobalAI</p>
              )}
              <p
                className={`p-3 rounded-lg ${message.sender === 'user'
                  ? 'bg-cyan-600 text-gray-100'
                  : 'bg-gray-700 text-gray-300'
                  } neon-border`}
              >
                <Message text={message.text}></Message>
              </p>
              {message.sender === 'bot' && (
                <button
                  className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  onClick={() => downloadFile(message.text)}
                >
                  Download Reply
                </button>
              )}
            </div>
          ))}
          {isLoading && (
            <p className="p-3 bg-gray-700 text-gray-300 rounded-lg neon-border">
              Typing...
            </p>
          )}
        </div>

        {/* Input Box */}
        {isSignedIn ? (
          <form
            onSubmit={handleSubmit}
            className="input-container flex items-center bg-gray-800 p-4 rounded-t-lg shadow-md neon-border"
          >
            <input
              type="text"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-grow bg-gray-700 text-gray-200 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 neon-input"
            />
            <button
              type="submit"
              className="ml-4 px-6 py-3 bg-cyan-600 text-gray-200 font-semibold rounded-lg transition-all duration-300 ease-in-out transform hover:shadow-[0_0_15px_2px_rgba(56,189,248,0.8)] focus:shadow-[0_0_15px_2px_rgba(56,189,248,0.8)] active:scale-95"
            >
              Send
            </button>
          </form>
        ) : (
          <div className="p-4 text-center text-gray-400">
            Please sign in to use the chatbot.
          </div>
        )}
      </div>
    </div>
  );
}

export default App;