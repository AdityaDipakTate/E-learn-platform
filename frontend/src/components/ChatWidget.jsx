// src/components/ChatWidget.jsx
import { useState, useRef, useEffect } from "react";

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { text: "Hi there! I am your AI Computer Science tutor. What are you struggling with today?", isBot: true }
  ]);
  
  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // 1. Add user message to UI
    const userMessage = { text: input, isBot: false };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // 2. Fetch the JWT token to prove the user is logged in
    const token = localStorage.getItem("token");
    if (!token) {
        setMessages((prev) => [...prev, { text: "Error: Please log in to use the AI tutor.", isBot: true }]);
        return;
    }

    // 3. Send the message to the FastAPI Backend
    try {
        const response = await fetch("http://127.0.0.1:8000/ai/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}` // Secure API call
            },
            body: JSON.stringify({ message: userMessage.text })
        });

        if (!response.ok) throw new Error("Backend connection failed.");

        const data = await response.json();
        
        // 4. Add the backend's response to the UI
        setMessages((prev) => [...prev, { text: data.reply, isBot: true }]);

    } catch (err) {
        setMessages((prev) => [...prev, { text: "⚠️ System error: Cannot reach the AI brain right now.", isBot: true }]);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* The Chat Window */}
      {isOpen && (
<div className="mb-4 w-80 sm:w-96 h-[500px] max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden transition-all duration-300">          
          {/* Header */}
          <div className="bg-blue-600 px-4 py-3 flex justify-between items-center text-white">
            <h3 className="font-bold text-lg flex items-center">
              <span className="mr-2">🤖</span> AI Tutor
            </h3>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-blue-200 text-xl font-bold transition"
            >
              &times;
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-grow p-4 overflow-y-auto bg-gray-50 flex flex-col space-y-3">
            {messages.map((msg, index) => (
              <div 
                key={index} 
                className={`max-w-[80%] p-3 rounded-xl text-sm ${
                  msg.isBot 
                    ? "bg-white border border-gray-200 text-gray-800 self-start rounded-tl-none shadow-sm" 
                    : "bg-blue-600 text-white self-end rounded-tr-none shadow-sm"
                }`}
              >
                {msg.text}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-grow px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
            <button 
              type="submit"
              className="ml-2 bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700 transition shadow-sm"
            >
              {/* Simple Send Icon */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </form>
        </div>
      )}

      {/* The Floating Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-xl transition transform hover:scale-110 flex items-center justify-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}
    </div>
  );
}