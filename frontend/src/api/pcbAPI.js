// simple axios wrapper to call your Flask backend
import axios from "axios";

const BASE = "http://127.0.0.1:5000/api";

export async function fetchPCB() {
  try {
    const r = await axios.get(`${BASE}/pcbsnapshot`);
    return r.data;
  } catch (e) {
    console.error("fetchPCB error", e);
    return [];
  }
}

export async function runScheduler(algorithm = "FCFS", quantum = 4) {
  try {
    const r = await axios.post(`${BASE}/schedule`, { algorithm, quantum });
    return r.data;
  } catch(e) {
    console.error("runScheduler error", e);
    return null;
  }
}

export async function fetchRealtime(limit = 20) {
  try {
    const r = await axios.get(`${BASE}/realtime?limit=${limit}`);
    return r.data;
  } catch(e) {
    console.error("fetchRealtime error", e);
    return [];
  }
}
