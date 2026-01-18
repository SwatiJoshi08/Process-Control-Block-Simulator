import React from "react";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
      <h1 className="text-3xl mb-6 font-bold">CPU Scheduler Dashboard</h1>
      <button
        onClick={() => navigate("/simulation")}
        className="bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg text-white font-semibold"
      >
        Next → Run Real-Time Simulation
      </button>
    </div>
  );
};

export default Dashboard;
