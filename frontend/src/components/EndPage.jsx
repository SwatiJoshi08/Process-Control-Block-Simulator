import React from "react";
import { useNavigate } from "react-router-dom";

const EndPage = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-blue-900 text-white">
      <h1 className="text-4xl font-bold mb-6">Simulation Completed 🎯</h1>
      <button
        onClick={() => navigate("/")}
        className="bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold hover:bg-blue-100 transition"
      >
        Back to Dashboard
      </button>
    </div>
  );
};

export default EndPage;
