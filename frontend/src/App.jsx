// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from './assets/vite.svg'
// import heroImg from './assets/hero.png'
// import './App.css'

// function App() {
//   const [count, setCount] = useState(0)

//   return (
//     <>
//       <section id="center">
//         <div className="hero">
//           <img src={heroImg} className="base" width="170" height="179" alt="" />
//           <img src={reactLogo} className="framework" alt="React logo" />
//           <img src={viteLogo} className="vite" alt="Vite logo" />
//         </div>
//       </section>
//     </>
//   )
// }

// export default App

// src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Auth from "./pages/Auth";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/auth" />} />
        <Route path="/auth" element={<Auth />} />
        
        {/* Placeholder for the next step! */}
        <Route path="/dashboard" element={
          <div className="flex items-center justify-center min-h-screen">
            <h1 className="text-4xl font-bold text-green-600">Login Successful! Welcome to the Dashboard.</h1>
          </div>
        } />
      </Routes>
    </Router>
  );
}

export default App;