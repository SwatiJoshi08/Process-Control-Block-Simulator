import React from "react";

export default function GanttChart({ gantt = [] }){
  // gantt expected: array of [pid, start, end, name] or objects. We'll handle both.
  const items = gantt.map(g => {
    if (Array.isArray(g)) return { pid: g[0], start: g[1], end: g[2], name: g[3] };
    return g;
  });

  return (
    <div className="panel">
      <h3 style={{textAlign:'center'}}>Gantt Chart</h3>
      <div className="gantt-row">
        {items.length === 0 && <div style={{color:'#6b7280'}}>No schedule yet</div>}
        {items.map((it, i) => (
          <div className="gantt-box" key={i}>
            {it.name ? `${it.name}` : `PID ${it.pid}`}
          </div>
        ))}
      </div>
    </div>
  );
}
