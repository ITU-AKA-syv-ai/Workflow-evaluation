import {BrowserRouter, Link, Route, Routes} from "react-router-dom";
import EvaluationDetails from "../evaluation-details/evaluation-details.tsx";

export default function Overview(){
    return (
        <div>
            <h1>Welcome to the overview</h1>
            <BrowserRouter>
              <section id="links">
                <ul>
                  <li>
                    <Link to="/evaluation-details">Go to evaluation details</Link>
                  </li>
                </ul>
              </section>

              <Routes>
                <Route path="/evaluation-details" element={<EvaluationDetails />} />
              </Routes>
            </BrowserRouter>
        </div>
    )
}