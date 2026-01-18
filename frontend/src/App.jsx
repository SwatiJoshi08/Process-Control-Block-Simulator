import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import RealTimeSimulation from "./components/RealTimeSimulation";
import SchedulerPage from "./components/SchedulerPage";
import EndPage from "./components/EndPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/realtime" element={<RealTimeSimulation />} />
        <Route path="/scheduler" element={<SchedulerPage />} />
        <Route path="/end" element={<EndPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
