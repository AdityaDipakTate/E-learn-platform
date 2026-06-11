// src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // 1. Security Check: Is the user actually logged in?
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/auth");
      return;
    }

    // 2. Fetch the CS courses from FastAPI
    const fetchCourses = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/courses");
        if (!response.ok) throw new Error("Failed to load courses from the server.");
        
        const data = await response.json();
        setCourses(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/auth");
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen text-xl text-gray-600">Loading courses...</div>;
  }

  return (
    <div className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-6xl mx-auto">
        
        {/* Header Section */}
        <div className="flex items-center justify-between mb-10">
          <h1 className="text-4xl font-bold text-gray-800">My Curriculum</h1>
          <button 
            onClick={handleLogout}
            className="px-4 py-2 text-sm font-semibold text-red-600 bg-red-100 rounded-lg hover:bg-red-200"
          >
            Log Out
          </button>
        </div>

        {error && <div className="p-4 mb-6 text-red-700 bg-red-100 rounded-lg">{error}</div>}

        {/* Course Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div key={course.id} className="flex flex-col p-6 bg-white border rounded-xl shadow-sm hover:shadow-md transition">
              <h2 className="text-2xl font-bold text-blue-700 mb-2">{course.title}</h2>
              <p className="flex-grow text-gray-600 mb-6">{course.description}</p>
              
              <button 
                onClick={() => navigate(`/course/${course.id}`)}
                className="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
              >
                Start Learning
              </button>
            </div>
          ))}
        </div>
        
        {courses.length === 0 && !error && (
          <p className="text-gray-500">No courses available at the moment.</p>
        )}

      </div>
    </div>
  );
}