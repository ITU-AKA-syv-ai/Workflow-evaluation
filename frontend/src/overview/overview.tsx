import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import type {
  AggregatedResultListItem,
  AggregatedResultEntityRaw,
} from "./models";
import { mapToAggregatedList } from "./models";
import "../styles/styles.css";

async function fetchEvaluationResults(): Promise<AggregatedResultListItem[]> {
  const res = await fetch("http://localhost:8000/results?offset=0&limit=10");
  const data: AggregatedResultEntityRaw[] = await res.json();

  return mapToAggregatedList(data);
}

export default function Overview() {
  const navigate = useNavigate();
  const [data, setData] = useState<AggregatedResultListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    let isMounted = true;

    fetchEvaluationResults().then((results) => {
      if (isMounted) {
        setData(results);
        setLoading(false);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) return <p>Loading...</p>;

  function setEvaluatorFilter(value: string): void {
    throw new Error("Function not implemented.");
  }

  function setStartDate(value: string): void {
    throw new Error("Function not implemented.");
  }

  function setEndDate(value: string): void {
    throw new Error("Function not implemented.");
  }

  function handleSort(arg0: string): void {
    throw new Error("Function not implemented.");
  }

  return (
    <div>
      <h1>Welcome to the overview</h1>
      <p>Here are the evaluation results:</p>
      <div className="filters">
        <input
          type="text"
          placeholder="Filter by evaluator..."
          onChange={(e) => setEvaluatorFilter(e.target.value)}
        />

        <input type="date" onChange={(e) => setStartDate(e.target.value)} />

        <input type="date" onChange={(e) => setEndDate(e.target.value)} />
      </div>
      <table className="results-table">
        <thead>
          <tr>
            <th onClick={() => handleSort("score")}>Score</th>
            <th>Evaluators</th>
            <th>Status</th>
            <th onClick={() => handleSort("timestamp")}>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr
              key={item.id}
              onClick={() => navigate(`/evaluation-details/${item.id}`)}
            >
              <td>{item.score}</td>
              <td>
                {item.evaluators.map((e, i) => (
                  <div key={i}>{e}</div>
                ))}
              </td>
              <td>{item.passed ? "Passed" : "Failed"}</td>

              <td>
                {item.timestamp ? item.timestamp.toLocaleString() : "N/A"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <button onClick={() => setPage((p) => p - 1)}>Previous</button>
        <span>Page {page}</span>
        <button onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </div>
  );
}
