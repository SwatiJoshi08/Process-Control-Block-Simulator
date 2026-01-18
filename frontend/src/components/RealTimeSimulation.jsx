import React from "react";
import { useNavigate } from "react-router-dom";
import RealTimeMonitor from "./RealTimeMonitor";

const RealTimeSimulation = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center">
      <h1 className="text-3xl font-bold mt-6">Real-Time Process Monitor</h1>

      {/* This component shows the live processes */}
      <RealTimeMonitor />

      <button
        onClick={() => navigate("/scheduler")}
        className="mt-8 mb-10 bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg text-white font-semibold transition"
      >
        Next → Scheduler Simulation
      </button>
    </div>
  );
};

export default RealTimeSimulation;
