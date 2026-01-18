#!/usr/bin/env python3
"""
Enhanced PCB Simulator with full CPU Scheduling algorithm implementations.

Implements:
- FCFS
- SJF (non-preemptive)
- SRTF (preemptive)
- Round Robin (user quantum)
- Priority (preemptive & non-preemptive)

Usage: Run the script. From the Startup Menu choose PCB Simulation.
When asked for algorithm, scheduler will run on a snapshot of current PCB list.
"""

import threading
import time
import random
import psutil
import os
import sys
import csv
import subprocess
from datetime import datetime
from tabulate import tabulate
from copy import deepcopy

# ---------- Configuration ----------
UPDATE_INTERVAL = 50.0   # seconds between refreshes
SIMULATED_PROCESS_COUNT = 8
CSV_EXPORT_FILENAME = "pcb_simulation_export.csv"
REALTIME_EXPORT_FILENAME = "realtime_process_export.csv"

# ---------- PCB States ----------
class PCBState:
    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    TERMINATED = "Terminated"

# ---------- PCB Structure ----------
class PCB:
    _pid_counter = 1000
    _pid_lock = threading.Lock()

    @classmethod
    def next_pid(cls):
        with cls._pid_lock:
            cls._pid_counter += 1
            return cls._pid_counter

    def __init__(self, name: str):
        self.pid = PCB.next_pid()
        self.name = name
        self.state = PCBState.NEW
        self.pc = random.randint(0, 1000)
        self.registers = {"R1": 0, "R2": 0, "R3": 0}
        # memory and cpu burst remain as integers
        self.memory_kb = random.randint(1024, 51200)
        self.priority = random.randint(0, 10)   # lower = higher priority
        self.cpu_burst = random.randint(10, 200)  # reduced upper bound for reasonable scheduling times
        self.io_burst = random.randint(10, 500)
        self.thread_count = random.randint(1, 8)
        self.cpu_usage = 0.0
        self.lock = threading.Lock()
        # arrival time (for scheduling) — small random to demonstrate different arrivals
        self.arrival_time = random.randint(0, 10)

    def to_row(self):
        regs = f"[R1={self.registers['R1']}, R2={self.registers['R2']}, R3={self.registers['R3']}, PC={self.pc}]"
        return [
            self.pid,
            self.name,
            self.state,
            f"{self.cpu_usage:.2f}",
            f"{self.memory_kb:,}",
            self.thread_count,
            regs,
            self.priority,
            self.cpu_burst,
            self.arrival_time
        ]

# ---------- Simulator Thread ----------
class SimulatedProcessThread(threading.Thread):
    def __init__(self, pcb: PCB, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.pcb = pcb
        self.stop_event = stop_event

    def run(self):
        with self.pcb.lock:
            self.pcb.state = PCBState.READY

        while not self.stop_event.is_set():
            with self.pcb.lock:
                if self.pcb.state == PCBState.READY and random.random() < 0.6:
                    self.pcb.state = PCBState.RUNNING
                elif self.pcb.state == PCBState.RUNNING:
                    self.pcb.pc += random.randint(1, 50)
                    self.pcb.registers = {r: random.randint(0, 1024) for r in ["R1", "R2", "R3"]}
                    base = min(100, max(0, (self.pcb.cpu_burst / 200.0) * 100))
                    fluct = random.uniform(-5, 10)
                    self.pcb.cpu_usage = max(0.0, min(100.0, base + fluct - self.pcb.priority))
                    if random.random() < 0.08:
                        self.pcb.state = PCBState.WAITING
                    elif random.random() < 0.02:
                        self.pcb.state = PCBState.TERMINATED
                elif self.pcb.state == PCBState.WAITING:
                    self.pcb.cpu_usage = random.uniform(0, 3)
                    if random.random() < 0.5:
                        self.pcb.state = PCBState.READY
                elif self.pcb.state == PCBState.TERMINATED:
                    self.pcb.cpu_usage = 0.0
            time.sleep(random.uniform(0.2, 1.0))

# ---------- PCB Manager ----------
class PCBManager:
    def __init__(self, count=SIMULATED_PROCESS_COUNT):
        self.pcbs = []
        self.threads = []
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # Realistic-ish names
        process_names = [
            "chrome.exe", "python3", "explorer.exe", "systemd",
            "notepad.exe", "spotify.exe", "discord.exe",
            "java", "cmd.exe", "vscode", "powershell.exe", "redis-server"
        ]

        for i in range(count):
            name = random.choice(process_names)
            self.pcbs.append(PCB(name=name))

    def start(self):
        # reset stop_event in case reused
        self.stop_event.clear()
        for pcb in self.pcbs:
            th = SimulatedProcessThread(pcb, self.stop_event)
            self.threads.append(th)
            th.start()

    def stop(self):
        self.stop_event.set()
        for t in self.threads:
            t.join(timeout=1.0)
        # clear threads list so manager can be restarted later if required
        self.threads = []

    def snapshot(self, sort_by=None, reverse=False):
        with self.lock:
            rows = [p.to_row() for p in self.pcbs]
        header_map = {
            'pid': 0, 'name': 1, 'state': 2, 'cpu': 3, 'memory': 4,
            'threads': 5, 'regs': 6, 'priority': 7, 'burst': 8, 'arrival': 9
        }
        if sort_by and sort_by in header_map:
            idx = header_map[sort_by]
            def key_fn(r):
                v = r[idx]
                if idx == 4:
                    return int(str(v).replace(",", ""))
                if idx in (0, 7, 8, 9):
                    return int(v)
                if idx == 3:
                    return float(v)
                return str(v).lower()
            rows.sort(key=key_fn, reverse=reverse)
        return rows

    def export_csv(self, filename=CSV_EXPORT_FILENAME):
        header = ["PID", "Name", "State", "CPU%", "Memory(KB)", "Threads", "Registers", "Priority", "Burst", "Arrival"]
        rows = self.snapshot()
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)
            return filename
        except Exception as e:
            return f"ERROR: {e}"

# ---------- Scheduling Utilities ----------
def compute_metrics(schedule_gantt, processes_info):
    """
    processes_info: dict pid -> dict with arrival, burst
    schedule_gantt: list of (pid, start, end)
    returns per-process stats dict and averages
    """
    stats = {}
    # Initialize
    for pid,info in processes_info.items():
        stats[pid] = {
            "arrival": info["arrival"],
            "burst": info["burst"],
            "start": None,
            "completion": None,
            "waiting": None,
            "turnaround": None
        }

    # Determine first start and completion times
    for entry in schedule_gantt:
        pid, s, e = entry
        if stats[pid]["start"] is None:
            stats[pid]["start"] = s
        stats[pid]["completion"] = e

    # compute waiting and turnaround
    total_wait = 0
    total_tat = 0
    n = len(stats)
    for pid, st in stats.items():
        st["turnaround"] = st["completion"] - st["arrival"]
        st["waiting"] = st["turnaround"] - st["burst"]
        total_wait += st["waiting"]
        total_tat += st["turnaround"]

    avg_wait = total_wait / n if n else 0
    avg_tat = total_tat / n if n else 0
    return stats, avg_wait, avg_tat

def print_gantt(gantt):
    """Print a textual Gantt timeline"""
    if not gantt:
        print("No schedule to show.")
        return
    # compact representation: [time] PID(name)
    print("Gantt Timeline:")
    for pid, s, e, name in gantt:
        print(f" | {s:3d} - {e:3d} : PID {pid} ({name})")
    # also a short line with times
    times = [str(s) for (_,s,_,_) in gantt] + [str(gantt[-1][2])]
    print("Timeline bounds:", " -> ".join(times))

# ---------- Scheduling Algorithms Implementations ----------
# All algorithms accept a list of dicts: {pid, name, arrival, burst, priority}

def fcfs_scheduler(procs):
    """First-Come First-Serve (non-preemptive)"""
    procs_sorted = sorted(procs, key=lambda p: (p["arrival"], p["pid"]))
    time_cursor = 0
    gantt = []
    processes_info = {}
    for p in procs_sorted:
        pid = p["pid"]
        processes_info[pid] = {"arrival": p["arrival"], "burst": p["burst"]}
        if time_cursor < p["arrival"]:
            # idle until arrival
            time_cursor = p["arrival"]
        start = time_cursor
        end = start + p["burst"]
        gantt.append((pid, start, end, p["name"]))
        time_cursor = end
    schedule = [(pid,s,e) for (pid,s,e,_) in gantt]
    stats, avg_w, avg_t = compute_metrics(schedule, processes_info)
    return gantt, stats, avg_w, avg_t

def sjf_nonpreemptive_scheduler(procs):
    """SJF non-preemptive"""
    procs_copy = deepcopy(procs)
    n = len(procs_copy)
    time_cursor = 0
    completed = 0
    gantt = []
    processes_info = {p["pid"]: {"arrival": p["arrival"], "burst": p["burst"]} for p in procs_copy}
    ready = []
    procs_by_arrival = sorted(procs_copy, key=lambda p: (p["arrival"], p["burst"], p["pid"]))
    i = 0
    while completed < n:
        # add arrived processes to ready
        while i < n and procs_by_arrival[i]["arrival"] <= time_cursor:
            p = procs_by_arrival[i]
            ready.append(p)
            i += 1
        if not ready:
            # jump to next arrival
            if i < n:
                time_cursor = procs_by_arrival[i]["arrival"]
            continue
        # pick shortest burst
        ready.sort(key=lambda x: (x["burst"], x["arrival"], x["pid"]))
        p = ready.pop(0)
        start = time_cursor
        end = start + p["burst"]
        gantt.append((p["pid"], start, end, p["name"]))
        time_cursor = end
        completed += 1
    schedule = [(pid,s,e) for (pid,s,e,_) in gantt]
    stats, avg_w, avg_t = compute_metrics(schedule, processes_info)
    return gantt, stats, avg_w, avg_t

def srtf_scheduler(procs):
    """SRTF (Shortest Remaining Time First) - preemptive"""
    procs_copy = deepcopy(procs)
    n = len(procs_copy)
    time_cursor = 0
    gantt = []
    processes_info = {p["pid"]: {"arrival": p["arrival"], "burst": p["burst"]} for p in procs_copy}
    remaining = {p["pid"]: p["burst"] for p in procs_copy}
    arrived = []
    procs_by_arrival = sorted(procs_copy, key=lambda p: (p["arrival"], p["pid"]))
    i = 0
    last_pid = None
    while True:
        # add arrived
        while i < n and procs_by_arrival[i]["arrival"] <= time_cursor:
            arrived.append(procs_by_arrival[i])
            i += 1
        # filter only those with positive remaining
        candidates = [p for p in arrived if remaining[p["pid"]] > 0]
        if not candidates:
            if i < n:
                # idle until next arrival
                time_cursor = procs_by_arrival[i]["arrival"]
                continue
            else:
                break
        # choose smallest remaining
        candidates.sort(key=lambda x: (remaining[x["pid"]], x["arrival"], x["pid"]))
        cur = candidates[0]
        pid = cur["pid"]
        # run for 1 unit (simulate preemption possibility each unit)
        start = time_cursor
        time_cursor += 1
        end = time_cursor
        remaining[pid] -= 1
        # record to gantt (merge contiguous slices of same pid)
        if gantt and gantt[-1][0] == pid and gantt[-1][2] == start:
            # extend previous
            gantt[-1] = (gantt[-1][0], gantt[-1][1], end, gantt[-1][3])
        else:
            gantt.append((pid, start, end, cur["name"]))
        # continue until all remaining zero
        if all(remaining[p["pid"]] == 0 for p in procs_copy):
            break
    schedule = [(pid,s,e) for (pid,s,e,_) in gantt]
    stats, avg_w, avg_t = compute_metrics(schedule, processes_info)
    return gantt, stats, avg_w, avg_t

def rr_scheduler(procs, quantum=4):
    """Round Robin"""
    procs_copy = deepcopy(procs)
    n = len(procs_copy)
    time_cursor = 0
    gantt = []
    processes_info = {p["pid"]: {"arrival": p["arrival"], "burst": p["burst"]} for p in procs_copy}
    remaining = {p["pid"]: p["burst"] for p in procs_copy}
    procs_by_arrival = sorted(procs_copy, key=lambda p: (p["arrival"], p["pid"]))
    queue = []
    i = 0
    # initialization: advance time to first arrival
    if procs_by_arrival:
        time_cursor = procs_by_arrival[0]["arrival"]
    while True:
        # enqueue arrivals at current time
        while i < n and procs_by_arrival[i]["arrival"] <= time_cursor:
            queue.append(procs_by_arrival[i])
            i += 1
        if not queue:
            if i < n:
                time_cursor = procs_by_arrival[i]["arrival"]
                continue
            else:
                break
        cur = queue.pop(0)
        pid = cur["pid"]
        run_time = min(quantum, remaining[pid])
        start = time_cursor
        end = start + run_time
        # record
        if gantt and gantt[-1][0] == pid and gantt[-1][2] == start:
            gantt[-1] = (gantt[-1][0], gantt[-1][1], end, gantt[-1][3])
        else:
            gantt.append((pid, start, end, cur["name"]))
        time_cursor = end
        remaining[pid] -= run_time
        # enqueue any newly arrived processes up to current time
        while i < n and procs_by_arrival[i]["arrival"] <= time_cursor:
            queue.append(procs_by_arrival[i])
            i += 1
        # if still has remaining time, re-enqueue
        if remaining[pid] > 0:
            queue.append(cur)
    schedule = [(pid,s,e) for (pid,s,e,_) in gantt]
    stats, avg_w, avg_t = compute_metrics(schedule, processes_info)
    return gantt, stats, avg_w, avg_t

def priority_nonpreemptive_scheduler(procs):
    """Priority non-preemptive: lower 'priority' value => higher priority"""
    procs_copy = deepcopy(procs)
    n = len(procs_copy)
    time_cursor = 0
    completed = 0
    gantt = []
    processes_info = {p["pid"]: {"arrival": p["arrival"], "burst": p["burst"]} for p in procs_copy}
    ready = []
    procs_by_arrival = sorted(procs_copy, key=lambda p: (p["arrival"], p["priority"], p["pid"]))
    i = 0
    while completed < n:
        while i < n and procs_by_arrival[i]["arrival"] <= time_cursor:
            ready.append(procs_by_arrival[i])
            i += 1
        if not ready:
            if i < n:
                time_cursor = procs_by_arrival[i]["arrival"]
            continue
        # pick by priority, then arrival, then pid
        ready.sort(key=lambda x: (x["priority"], x["arrival"], x["pid"]))
        p = ready.pop(0)
        start = time_cursor
        end = start + p["burst"]
        gantt.append((p["pid"], start, end, p["name"]))
        time_cursor = end
        completed += 1
    schedule = [(pid,s,e) for (pid,s,e,_) in gantt]
    stats, avg_w, avg_t = compute_metrics(schedule, processes_info)
    return gantt, stats, avg_w, avg_t

def priority_preemptive_scheduler(procs):
    """Priority preemptive (lower number -> higher priority)"""
    procs_copy = deepcopy(procs)
    n = len(procs_copy)
    time_cursor = 0
    gantt = []
    processes_info = {p["pid"]: {"arrival": p["arrival"], "burst": p["burst"]} for p in procs_copy}
    remaining = {p["pid"]: p["burst"] for p in procs_copy}
    procs_by_arrival = sorted(procs_copy, key=lambda p: (p["arrival"], p["priority"], p["pid"]))
    arrived = []
    i = 0
    while True:
        while i < n and procs_by_arrival[i]["arrival"] <= time_cursor:
            arrived.append(procs_by_arrival[i])
            i += 1
        candidates = [p for p in arrived if remaining[p["pid"]] > 0]
        if not candidates:
            if i < n:
                time_cursor = procs_by_arrival[i]["arrival"]
                continue
            else:
                break
        # choose process with highest priority (lowest priority number)
        candidates.sort(key=lambda x: (x["priority"], x["arrival"], x["pid"]))
        cur = candidates[0]
        pid = cur["pid"]
        # run one time unit
        start = time_cursor
        time_cursor += 1
        end = time_cursor
        remaining[pid] -= 1
        if gantt and gantt[-1][0] == pid and gantt[-1][2] == start:
            gantt[-1] = (gantt[-1][0], gantt[-1][1], end, gantt[-1][3])
        else:
            gantt.append((pid, start, end, cur["name"]))
        if all(remaining[p["pid"]] == 0 for p in procs_copy):
            break
    schedule = [(pid,s,e) for (pid,s,e,_) in gantt]
    stats, avg_w, avg_t = compute_metrics(schedule, processes_info)
    return gantt, stats, avg_w, avg_t

# ---------- Real-Time Monitor ----------
def fetch_system_processes(limit=25):
    rows = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'num_threads']):
        try:
            info = proc.info
            pid = info.get('pid', '')
            name = info.get('name', '') or ''
            cpu = info.get('cpu_percent', 0.0)
            mem_rss = getattr(info.get('memory_info', None), 'rss', 0) // 1024
            status = info.get('status', '')
            threads = info.get('num_threads', 0)
            rows.append([pid, name, f"{cpu:.2f}", f"{mem_rss:,}", status, threads])
            if len(rows) >= limit:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    rows.sort(key=lambda r: float(r[2]), reverse=True)
    return rows

def export_realtime_csv(filename=REALTIME_EXPORT_FILENAME, rows=None):
    header = ["PID", "ProcessName", "CPU%", "Memory(KB)", "Status", "Threads"]
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            if rows:
                writer.writerows(rows)
        return filename
    except Exception as e:
        return f"ERROR: {e}"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def realtime_monitor_loop():
    print("Starting real-time process monitor. Press Ctrl+C to return.")
    for p in psutil.process_iter():
        try:
            p.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    last_snapshot = []
    try:
        while True:
            clear_screen()
            procs = fetch_system_processes(limit=20)
            last_snapshot = procs
            headers = ["PID", "ProcessName", "CPU%", "Memory(KB)", "Status", "Threads"]
            print(f"Real-time processes (refresh every {UPDATE_INTERVAL}s)\n")
            print(tabulate(procs, headers=headers, tablefmt="github"))
            print("\nPress Ctrl+C to exit monitoring.")
            time.sleep(UPDATE_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping monitoring... Exporting to CSV...")
        filename = export_realtime_csv(rows=last_snapshot)
        if filename.startswith("ERROR"):
            print("Export failed:", filename)
        else:
            print(f"Exported real-time snapshot to:\n{filename}")
            try:
                if os.name == "nt":
                    os.startfile(filename)
                elif sys.platform == "darwin":
                    subprocess.call(["open", filename])
                else:
                    subprocess.call(["xdg-open", filename])
            except Exception as e:
                print(f"(Could not auto-open CSV: {e})")
        time.sleep(0.6)

# ---------- PCB Simulation Menu & Integration ----------
def select_scheduling_algorithm():
    clear_screen()
    print("Select CPU Scheduling Algorithm:\n")
    algorithms = [
        "1. First Come First Serve (FCFS)",
        "2. Shortest Job First (SJF) - Non-preemptive",
        "3. Shortest Remaining Time First (SRTF) - Preemptive",
        "4. Round Robin (RR)",
        "5. Priority Scheduling (Preemptive)",
        "6. Priority Scheduling (Non-Preemptive)"
    ]
    for alg in algorithms:
        print(alg)
    choice = input("\nEnter your choice [1-6]: ").strip()
    mapping = {
        "1": "FCFS", "2": "SJF", "3": "SRTF", "4": "Round Robin",
        "5": "Priority (Preemptive)", "6": "Priority (Non-Preemptive)"
    }
    return mapping.get(choice, "FCFS"), choice

def show_schedule_and_stats(gantt, stats, avg_w, avg_t):
    clear_screen()
    # Gantt lines with names
    print_gantt(gantt)
    print("\nPer-process results:")
    rows = []
    headers = ["PID", "Arrival", "Burst", "Start", "Completion", "Waiting", "Turnaround"]
    for pid, s in sorted(stats.items(), key=lambda kv: kv[0]):
        rows.append([
            pid, s["arrival"], s["burst"], s["start"], s["completion"],
            s["waiting"], s["turnaround"]
        ])
    print(tabulate(rows, headers=headers, tablefmt="github"))
    print(f"\nAverage waiting time: {avg_w:.2f}")
    print(f"Average turnaround time: {avg_t:.2f}")

def collect_procs_for_scheduling(manager: PCBManager):
    """
    Create a list of processes (dicts) to feed to the schedulers.
    We take a snapshot to avoid races.
    Each dict: pid, name, arrival, burst, priority
    """
    rows = manager.snapshot()
    # snapshot rows: [PID, Name, State, CPU%, Memory(KB), Threads, Registers, Priority, Burst, Arrival]
    procs = []
    for r in rows:
        pid = int(r[0])
        name = r[1]
        priority = int(r[7])
        burst = int(r[8])
        arrival = int(r[9])
        procs.append({
            "pid": pid,
            "name": name,
            "arrival": arrival,
            "burst": burst,
            "priority": priority
        })
    return procs

def pcb_simulation_menu(manager: PCBManager):
    algo_name, algo_choice = select_scheduling_algorithm()
    quantum = None
    if algo_choice == "4":
        # Round Robin
        try:
            q = int(input("Enter time quantum (positive integer, default 4): ").strip() or "4")
            if q <= 0:
                q = 4
        except:
            q = 4
        quantum = q

    # collect snapshot for scheduling
    procs = collect_procs_for_scheduling(manager)
    if not procs:
        print("No simulated processes to schedule.")
        input("\nPress Enter to continue...")
        return

    # run the selected scheduler
    if algo_choice == "1":
        gantt, stats, avg_w, avg_t = fcfs_scheduler(procs)
    elif algo_choice == "2":
        gantt, stats, avg_w, avg_t = sjf_nonpreemptive_scheduler(procs)
    elif algo_choice == "3":
        gantt, stats, avg_w, avg_t = srtf_scheduler(procs)
    elif algo_choice == "4":
        gantt, stats, avg_w, avg_t = rr_scheduler(procs, quantum=quantum)
    elif algo_choice == "5":
        gantt, stats, avg_w, avg_t = priority_preemptive_scheduler(procs)
    elif algo_choice == "6":
        gantt, stats, avg_w, avg_t = priority_nonpreemptive_scheduler(procs)
    else:
        gantt, stats, avg_w, avg_t = fcfs_scheduler(procs)

    # show results
    show_schedule_and_stats(gantt, stats, avg_w, avg_t)

    # After scheduling, show a snapshot with final states set to Terminated and attach completion times
    # Create a display table that preserves original PCB columns and appends Completion/Waiting/Turnaround
    completion_map = {pid: st["completion"] for pid,st in stats.items()}
    rows = manager.snapshot()
    display_rows = []
    headers = ["PID", "Name", "State", "CPU%", "Memory(KB)", "Threads", "Registers", "Priority", "Burst", "Arrival", "Completion", "Waiting", "Turnaround"]
    for r in rows:
        pid = int(r[0])
        comp = completion_map.get(pid, "")
        st = stats.get(pid, {})
        waiting = st.get("waiting", "")
        tat = st.get("turnaround", "")
        # Mark state terminated (simulation result); keep CPU% as-is
        display_rows.append([r[0], r[1], "Terminated", r[3], r[4], r[5], r[6], r[7], r[8], r[9], comp, waiting, tat])

    print("\nFinal snapshot (post-scheduling):")
    print(tabulate(display_rows, headers=headers, tablefmt="github"))
    input("\nPress Enter to continue...")

# ---------- Printing PCB Table (for normal view) ----------
def print_pcb_table(manager: PCBManager, sort_by=None, reverse=False):
    headers = ["PID", "Name", "State", "CPU%", "Memory(KB)", "Threads", "Registers", "Priority", "Burst", "Arrival"]
    rows = manager.snapshot(sort_by=sort_by, reverse=reverse)
    print(tabulate(rows, headers=headers, tablefmt="github"))

# ---------- Startup / Menus ----------
def startup_menu():
    manager = None
    while True:
        clear_screen()
        print("===== Startup Menu =====")
        print("1. Run Real-Time Process Monitoring") 
        print("2. Open PCB Simulation")
        print("3. Exit")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            realtime_monitor_loop()
        elif choice == "2":
            # Create manager and start simulated process threads (they will keep updating simulated PCBs)
            manager = PCBManager(count=SIMULATED_PROCESS_COUNT)
            manager.start()
            try:
                while True:
                    clear_screen()
                    print("===== PCB Simulation Supervisor =====")
                    print("1. Show PCB Simulation (one snapshot)")
                    print("2. Continuously update PCB Simulation (Ctrl+C to stop)")
                    print("3. Run scheduling algorithms on snapshot")
                    print("4. Sort options")
                    print("5. Export current PCB snapshot to CSV (auto-open)")
                    print("6. Return to main menu")
                    c = input("Enter choice: ").strip()
                    if c == "1":
                        clear_screen()
                        print_pcb_table(manager)
                        input("\nPress Enter to continue...")
                    elif c == "2":
                        print("Continuous PCB simulation (press Ctrl+C to stop)...")
                        try:
                            while True:
                                clear_screen()
                                print_pcb_table(manager)
                                time.sleep(UPDATE_INTERVAL)
                        except KeyboardInterrupt:
                            print("\nStopped continuous simulation. Returning...")
                            time.sleep(0.6)
                    elif c == "3":
                        pcb_simulation_menu(manager)
                    elif c == "4":
                        clear_screen()
                        print("Sort by: pid | name | state | cpu | memory | threads | priority | burst | arrival")
                        s = input("Enter sort key (or blank to cancel): ").strip().lower()
                        if not s:
                            continue
                        rev = input("Reverse order? (y/N): ").strip().lower() == 'y'
                        clear_screen()
                        print_pcb_table(manager, sort_by=s, reverse=rev)
                        input("\nPress Enter to continue...")
                    elif c == "5":
                        filename = manager.export_csv()
                        if filename.startswith("ERROR"):
                            print("Export failed:", filename)
                        else:
                            print(f" Exported current PCB snapshot to:\n{filename}")
                            try:
                                if os.name == "nt":
                                    os.startfile(filename)
                                elif sys.platform == "darwin":
                                    subprocess.call(["open", filename])
                                else:
                                    subprocess.call(["xdg-open", filename])
                            except Exception as e:
                                print(f"(Could not auto-open CSV: {e})")
                        input("\nPress Enter to continue...")
                    elif c == "6":
                        break
                    else:
                        print("Invalid choice. Try again.")
                        time.sleep(0.8)
            finally:
                if manager:
                    manager.stop()
        elif choice == "3": 
            print("Exiting program...")
            break
        else:
            print("Invalid choice. Try again.")
            time.sleep(0.8)

if __name__ == "__main__":
    try:
        startup_menu()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(0)
