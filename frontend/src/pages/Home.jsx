import Navbar from "../pages/Navbar";
export default function Home() {
  return (
    <>
      <Navbar />
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-r from-blue-100 to-purple-200">
        <div className="text-center p-8 bg-white rounded-lg shadow-lg">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">Welcome to AI CS E-Learning!</h1>
          <p className="text-lg text-gray-600 mb-6">Your personalized curriculum for mastering computer science with AI.</p>
          <a href="/dashboard" className="inline-block px-6 py-3 text-lg font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition">
            Get Started
          </a>
        </div>
      </div>
    </>
  );
}