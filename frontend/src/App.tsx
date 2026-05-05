import './App.css'
import "./styles/styles.css"
import Dashboard from './dashboard/dashboard.tsx'
import Overview from './overview/overview.tsx'
import EvaluationDetails from "./evaluation-details/evaluation-details.tsx";

import {BrowserRouter, Routes, Route, useNavigate} from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <>
      <h1>Workflow Evaluation</h1>
      <center>
      <div className="link_container">
        <div className="link" onClick={() => navigate("/overview")}>
          <p><strong>Overview. </strong>Browse an overview of previous evaluations.</p>
        </div>

        <div className="link" onClick={() => navigate("/dashboard")}>
          <p><strong>Dashboard. </strong>View statistics about previous evaluations.</p>
        </div>
      </div>
      </center>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/details/:id" element={<EvaluationDetails />} />
      </Routes>
    </BrowserRouter>
  );
}
