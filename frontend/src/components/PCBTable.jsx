import React from "react";

export default function PCBTable({ rows = [] }){
  return (
    <table className="table panel" aria-label="PCB table">
      <thead>
        <tr>
          <th>PID</th><th>Name</th><th>State</th><th>CPU %</th>
          <th>Memory</th><th>Threads</th><th>Priority</th><th>Burst</th><th>Arrival</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.pid}>
            <td>{r.pid}</td>
            <td>{r.name}</td>
            <td>{r.state}</td>
            <td>{r.cpu}</td>
            <td>{r.memory}</td>
            <td>{r.threads}</td>
            <td>{r.priority}</td>
            <td>{r.burst}</td>
            <td>{r.arrival}</td>
          </tr>
        ))}
        {rows.length === 0 && (
          <tr><td colSpan="9" style={{textAlign:'center', color:'#6b7280'}}>No processes (click Run Simulation)</td></tr>
        )}
      </tbody>
    </table>
  );
}
