import React from "react";
import { useNavigate } from "react-router-dom";
import RealTimeMonitor from "./RealTimeMonitor";

const Simulation = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center">
      <h1 className="text-3xl font-bold mt-6">CPU Scheduling Simulation</h1>

      <RealTimeMonitor />

      <button
        onClick={() => navigate("/dashboard")}
        className="mt-8 mb-10 bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg text-white font-semibold transition"
      >
        ← Back to Dashboard
      </button>
    </div>
  );
};

export default Simulation;
