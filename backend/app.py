from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import random
from pcb_simulator import (
    PCBManager,
    fcfs_scheduler,
    sjf_nonpreemptive_scheduler,
    srtf_scheduler,
    rr_scheduler,
    priority_preemptive_scheduler,
    priority_nonpreemptive_scheduler
)

# -------------------- Flask App Setup --------------------
app = Flask(__name__)
CORS(app)

# Initialize PCB Manager
manager = PCBManager(count=8)
manager.start()

# -------------------- API: PCB Snapshot --------------------
@app.route("/api/pcbsnapshot", methods=["GET"])
def get_pcb_snapshot():
    """Return current PCB snapshot"""
    rows = manager.snapshot()
    data = []
    for r in rows:
        data.append({
            "pid": r[0],
            "name": r[1],
            "state": r[2],
            "cpu": r[3],
            "memory": r[4],
            "threads": r[5],
            "priority": r[7],
            "burst": r[8],
            "arrival": r[9],
        })
    return jsonify(data)

# -------------------- API: Run Scheduling --------------------
@app.route("/api/schedule", methods=["POST"])
def run_schedule():
    """Run selected CPU scheduling algorithm"""
    payload = request.get_json(force=True)
    algo = payload.get("algorithm", "FCFS")
    quantum = int(payload.get("quantum", 4))

    procs = [
        {
            "pid": int(r[0]),
            "name": r[1],
            "arrival": int(r[9]),
            "burst": int(r[8]),
            "priority": int(r[7]),
        }
        for r in manager.snapshot()
    ]

    # Select algorithm
    if algo == "FCFS":
        gantt, stats, avg_w, avg_t = fcfs_scheduler(procs)
    elif algo == "SJF":
        gantt, stats, avg_w, avg_t = sjf_nonpreemptive_scheduler(procs)
    elif algo == "SRTF":
        gantt, stats, avg_w, avg_t = srtf_scheduler(procs)
    elif algo == "RR":
        gantt, stats, avg_w, avg_t = rr_scheduler(procs, quantum)
    elif algo == "Priority (Preemptive)":
        gantt, stats, avg_w, avg_t = priority_preemptive_scheduler(procs)
    else:
        gantt, stats, avg_w, avg_t = priority_nonpreemptive_scheduler(procs)

    return jsonify({
        "gantt": gantt,
        "avg_wait": avg_w,
        "avg_tat": avg_t
    })

# -------------------- API: Real-time Processes --------------------
@app.route("/api/realtime", methods=["GET"])
def get_realtime_processes():
    """Return live system processes for the real-time monitor"""
    limit = int(request.args.get("limit", 20))
    procs = []

    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'num_threads']):
        try:
            procs.append({
                "pid": p.info['pid'],
                "name": p.info['name'],
                "cpu": p.info['cpu_percent'],
                "memory": round(p.info['memory_percent'], 2),
                "status": p.info['status'],
                "threads": p.info['num_threads']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:limit]
    return jsonify(procs)

# -------------------- Main --------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
