import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const SchedulerPage = () => {
  const [selectedAlgo, setSelectedAlgo] = useState("FCFS");
  const [ganttChart, setGanttChart] = useState([]);
  const [avgWaiting, setAvgWaiting] = useState(0);
  const [avgTurnaround, setAvgTurnaround] = useState(0);
  const navigate = useNavigate();

  // --- Static 8 processes (ordered for FCFS Gantt chart) ---
  const staticProcesses = [
    { pid: 1001, name: "chrome.exe", arrival: 0, burst: 4, priority: 2 },
    { pid: 1002, name: "cmd.exe", arrival: 1, burst: 5, priority: 3 },
    { pid: 1003, name: "discord.exe", arrival: 2, burst: 3, priority: 1 },
    { pid: 1004, name: "vscode", arrival: 3, burst: 6, priority: 2 },
    { pid: 1005, name: "redis-server", arrival: 4, burst: 4, priority: 2 },
    { pid: 1006, name: "explorer.exe", arrival: 5, burst: 5, priority: 1 },
    { pid: 1007, name: "java", arrival: 6, burst: 7, priority: 3 },
    { pid: 1008, name: "redis-server", arrival: 7, burst: 3, priority: 2 },
  ];

  // --- Run the selected scheduling algorithm ---
  const runSimulation = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/schedule", {
        algorithm: selectedAlgo,
      });
      setGanttChart(res.data.gantt || []);
      setAvgWaiting(res.data.avg_wait || 0);
      setAvgTurnaround(res.data.avg_tat || 0);
    } catch (err) {
      console.error("Error running scheduler:", err);
      alert("⚠️ Failed to run scheduler! Please ensure backend is running.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center py-10">
      <h1 className="text-3xl font-bold mb-8">⚙️ Scheduler Simulation</h1>

      {/* Controls */}
      <div className="flex space-x-4 mb-6">
        <select
          className="bg-black text-white border border-gray-600 px-4 py-2 rounded"
          value={selectedAlgo}
          onChange={(e) => setSelectedAlgo(e.target.value)}
        >
          <option value="FCFS">FCFS (First Come First Serve)</option>
          <option value="SJF">SJF (Shortest Job First)</option>
          <option value="SRTF">SRTF (Shortest Remaining Time First)</option>
          <option value="RR">Round Robin</option>
          <option value="Priority (Preemptive)">Priority (Preemptive)</option>
          <option value="Priority (Non-Preemptive)">
            Priority (Non-Preemptive)
          </option>
        </select>

        <button
          onClick={runSimulation}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded shadow"
        >
          Run Simulation
        </button>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-2 gap-6 w-11/12 max-w-6xl">
        {/* LEFT SIDE: Static Process Table */}
        <div className="bg-gray-800 rounded-xl shadow-md p-5 overflow-auto">
          <h2 className="text-xl font-semibold mb-4 text-center">
            📋 Process Details (Static)
          </h2>
          <table className="table-auto w-full border border-gray-700">
            <thead>
              <tr className="bg-gray-700">
                <th className="border px-2 py-1">PID</th>
                <th className="border px-2 py-1">Name</th>
                <th className="border px-2 py-1">Arrival</th>
                <th className="border px-2 py-1">Burst</th>
                <th className="border px-2 py-1">Priority</th>
              </tr>
            </thead>
            <tbody>
              {staticProcesses.map((p, i) => (
                <tr key={i} className="text-center hover:bg-gray-700">
                  <td className="border px-2 py-1">{p.pid}</td>
                  <td className="border px-2 py-1">{p.name}</td>
                  <td className="border px-2 py-1">{p.arrival}</td>
                  <td className="border px-2 py-1">{p.burst}</td>
                  <td className="border px-2 py-1">{p.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* RIGHT SIDE: Gantt Chart */}
        <div className="bg-gray-800 rounded-xl shadow-md p-5 text-center">
          <h2 className="text-xl font-semibold mb-4">📊 Gantt Chart</h2>
          <div className="flex flex-wrap justify-center">
            {ganttChart.length === 0 ? (
              <p className="text-gray-400">
                No chart yet. Run an algorithm to see output.
              </p>
            ) : (
              ganttChart.map((p, i) => (
                <div
                  key={i}
                  className="m-1 px-3 py-2 bg-blue-600 rounded shadow text-sm"
                >
                  {p[3]} ({p[0]})
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Averages */}
      <div className="mt-8 bg-gray-800 px-6 py-3 rounded-lg text-center w-2/3">
        <p>Average Waiting Time: {avgWaiting.toFixed(2)}</p>
        <p>Average Turnaround Time: {avgTurnaround.toFixed(2)}</p>
      </div>

      {/* Next Button */}
      <button
        onClick={() => navigate("/end")}
        className="mt-6 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg shadow-lg"
      >
        Next → End Simulation
      </button>
    </div>
  );
};

export default SchedulerPage;
