import React from "react";
import { useNavigate } from "react-router-dom";

const LandingPage = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-blue-700 text-white">
      <h1 className="text-4xl font-bold mb-6 text-center">
        Dynamic Process Control Block (PCB) Simulator
      </h1>
      <button
        onClick={() => navigate("/realtime")}
        className="bg-white text-blue-700 font-semibold px-6 py-3 rounded-lg shadow-md hover:bg-blue-100 transition"
      >
        Next →
      </button>
    </div>
  );
};

export default LandingPage;
