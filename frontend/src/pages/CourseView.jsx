// src/pages/CourseView.jsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";

export default function CourseView() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  
  const [lessons, setLessons] = useState([]);
  const [activeLesson, setActiveLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [completionMessage, setCompletionMessage] = useState("");

  useEffect(() => {
    const fetchLessons = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/auth");
        return;
      }

      try {
        // Fetch lessons for this specific course
        const response = await fetch(`http://127.0.0.1:8000/courses/${courseId}/lessons`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error("Failed to load lessons.");
        
        const data = await response.json();
        setLessons(data);
        if (data.length > 0) setActiveLesson(data[0]); // Default to first lesson
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchLessons();
  }, [courseId, navigate]);

  const markAsCompleted = async () => {
    const token = localStorage.getItem("token");
    setCompletionMessage("");
    
    try {
      const response = await fetch("http://127.0.0.1:8000/progress/update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ lesson_id: activeLesson.id, is_completed: true })
      });

      if (!response.ok) throw new Error("Could not update progress");
      setCompletionMessage("🎉 Lesson marked as completed!");
      
      // Hide message after 3 seconds
      setTimeout(() => setCompletionMessage(""), 3000);
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="flex justify-center mt-20 text-xl">Loading lessons...</div>;
  if (error) return <div className="flex justify-center mt-20 text-red-500">{error}</div>;

  return (
    <div className="flex min-h-screen bg-gray-50">
      
      {/* Sidebar: Lesson Navigation */}
      <div className="w-1/4 bg-white border-r shadow-sm p-6 flex flex-col">
        <button onClick={() => navigate("/dashboard")} className="text-blue-600 hover:underline mb-6 text-sm font-semibold">
          &larr; Back to Dashboard
        </button>
        <h2 className="text-xl font-bold text-gray-800 mb-4">Course Lessons</h2>
        <div className="space-y-2 flex-grow">
          {lessons.map((lesson) => (
            <button
              key={lesson.id}
              onClick={() => { setActiveLesson(lesson); setCompletionMessage(""); }}
              className={`w-full text-left px-4 py-3 rounded-lg transition ${
                activeLesson?.id === lesson.id 
                  ? "bg-blue-100 text-blue-800 font-bold border-l-4 border-blue-600" 
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {lesson.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content: Lesson Viewer */}
      <div className="w-3/4 p-10 overflow-y-auto">
        {activeLesson ? (
          <div className="max-w-3xl mx-auto bg-white p-10 rounded-xl shadow-sm border">
            <h1 className="text-4xl font-extrabold text-gray-900 mb-6">{activeLesson.title}</h1>
            
            {/* Optional Video Embed */}
            {activeLesson.video_url && (
              <div className="mb-8 aspect-w-16 aspect-h-9">
                <iframe 
                  src={activeLesson.video_url} 
                  className="w-full h-96 rounded-lg shadow-sm"
                  allowFullScreen
                  title="Lesson Video"
                ></iframe>
              </div>
            )}

            {/* Markdown Content rendered beautifully */}
            <div className="prose prose-blue max-w-none text-gray-700 leading-relaxed">
              <ReactMarkdown>{activeLesson.content}</ReactMarkdown>
            </div>

            <hr className="my-10" />

            {/* Progress Tracking Action */}
            <div className="flex flex-col items-center">
              {completionMessage && <div className="mb-4 text-green-600 font-bold">{completionMessage}</div>}
              <button 
                onClick={markAsCompleted}
                className="px-8 py-3 bg-green-600 text-white font-bold rounded-full shadow hover:bg-green-700 transition transform hover:scale-105"
              >
                Mark as Completed
              </button>
            </div>
          </div>
        ) : (
          <div className="text-gray-500">Select a lesson to begin.</div>
        )}
      </div>
    </div>
  );
}