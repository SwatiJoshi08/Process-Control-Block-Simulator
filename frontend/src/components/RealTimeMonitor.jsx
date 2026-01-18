import React, { useEffect, useState } from "react";
import axios from "axios";

const BASE_URL = "http://127.0.0.1:5000/api/realtime";

const RealTimeMonitor = () => {
  const [processes, setProcesses] = useState([]);
  const [loading, setLoading] = useState(true);

  // Function to fetch process data
  const fetchProcesses = async () => {
    try {
      const res = await axios.get(BASE_URL + "?limit=20");
      setProcesses(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching real-time data:", err);
      setLoading(false);
    }
  };

  // Automatically update every 5 seconds
  useEffect(() => {
    fetchProcesses(); // initial load
    const interval = setInterval(fetchProcesses, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mt-6 bg-gray-900 rounded-2xl shadow-lg p-6 w-11/12 max-w-6xl text-white overflow-auto">
      <h2 className="text-2xl font-semibold mb-4 text-center">
        🧠 Real-Time Process Snapshot
      </h2>

      {loading ? (
        <p className="text-center text-gray-400">Loading process data...</p>
      ) : processes.length === 0 ? (
        <p className="text-center text-gray-400">No processes found.</p>
      ) : (
        <table className="table-auto w-full border-collapse border border-gray-700">
          <thead>
            <tr className="bg-gray-800 text-gray-200">
              <th className="border border-gray-700 px-4 py-2">PID</th>
              <th className="border border-gray-700 px-4 py-2">Process Name</th>
              <th className="border border-gray-700 px-4 py-2">CPU %</th>
              <th className="border border-gray-700 px-4 py-2">Memory %</th>
              <th className="border border-gray-700 px-4 py-2">Status</th>
              <th className="border border-gray-700 px-4 py-2">Threads</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((p, index) => (
              <tr
                key={index}
                className={`${
                  index % 2 === 0 ? "bg-gray-800" : "bg-gray-700"
                } hover:bg-gray-600 transition`}
              >
                <td className="border border-gray-700 px-4 py-2 text-center">
                  {p.pid}
                </td>
                <td className="border border-gray-700 px-4 py-2 text-center">
                  {p.name || "—"}
                </td>
                <td className="border border-gray-700 px-4 py-2 text-center">
                  {p.cpu?.toFixed(1)}
                </td>
                <td className="border border-gray-700 px-4 py-2 text-center">
                  {p.memory?.toFixed(2)}
                </td>
                <td className="border border-gray-700 px-4 py-2 text-center">
                  {p.status}
                </td>
                <td className="border border-gray-700 px-4 py-2 text-center">
                  {p.threads}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default RealTimeMonitor;
