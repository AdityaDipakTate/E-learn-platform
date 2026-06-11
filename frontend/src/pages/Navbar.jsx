
export default function Navbar() {
  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <a href="/home" className="text-xl font-bold text-gray-800">
              AI CS E-Learning
            </a>
          </div>
          <div className="flex items-center">
            <a href="/dashboard" className="text-gray-700 hover:text-blue-600">
              Dashboard
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}