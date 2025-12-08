import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./Home";
import ExamMonitor from "./ExamMonitor";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/monitor" element={<ExamMonitor />} />
      </Routes>
    </Router>
  );
}

export default App;