import { useNavigate } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";
import type {
  AggregatedResultListItem,
  AggregatedResultEntityRaw,
  Evaluators,
  EvaluatorsRaw,
} from "./models";
import { mapToAggregatedList, mapEvaluators } from "./models";
import "../styles/styles.css";

const PAGE_SIZE = 10;

async function fetchEvaluationResults(
  offset: number,
  limit: number,
): Promise<AggregatedResultListItem[]> {
  console.log(offset + " " + limit);
  const res = await fetch(
    `http://localhost:8000/results?offset=${offset}&limit=${limit}`,
  );
  const data: AggregatedResultEntityRaw[] = await res.json();

  return mapToAggregatedList(data);
}

async function getEvaluators(): Promise<Evaluators[]> {
  const res = await fetch("http://localhost:8000/evaluators");
  const data: EvaluatorsRaw[] = await res.json();
  return mapEvaluators(data);
}

export default function Overview() {
  const navigate = useNavigate();
  const [allData, setAllData] = useState<AggregatedResultListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [evaluators, setEvaluators] = useState<Evaluators[]>([]);
  const [evaluatorFilter, setEvaluatorFilterState] = useState<string>("");
  const [startDate, setStartDateFilterState] = useState<string>("");
  const [endDate, setEndDateFilterState] = useState<string>("");
  const [sortKey, setSortKey] = useState<"score" | "timestamp" | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const tableData = useMemo(() => {
    if (!allData || allData.length === 0) return [];
    //filration
    let filtered = allData.filter((item) => {
      if (
        evaluatorFilter &&
        !item.evaluators.includes(evaluatorFilter.replaceAll("_", " "))
      ) {
        return false;
      }
      const ts = item.timestamp ? new Date(item.timestamp) : null;

      if (startDate) {
        const sd = new Date(startDate);
        sd.setHours(0, 0, 0, 0);
        if (!ts || ts < sd) return false;
      }

      if (endDate) {
        const ed = new Date(endDate);
        ed.setHours(23, 59, 59, 999);
        if (!ts || ts > ed) return false;
      }
      return true;
    });
    // sorting
    if (sortKey) {
      filtered = [...filtered].sort((a, b) => {
        let aValue: number = 0;
        let bValue: number = 0;

        if (sortKey === "score") {
          aValue = a.score;
          bValue = b.score;
        }
        if (sortKey === "timestamp") {
          aValue = a.timestamp ? a.timestamp.getTime() : 0;
          bValue = b.timestamp ? b.timestamp.getTime() : 0;
        }

        if (sortDirection === "asc") {
          return aValue - bValue;
        } else {
          return bValue - aValue;
        }
      });
    }

    return filtered;
  }, [allData, evaluatorFilter, startDate, endDate, sortKey, sortDirection]);

  useEffect(() => {
    let isMounted = true;

    const offset = (page - 1) * PAGE_SIZE;

    getEvaluators().then((evaluatorList) => {
      setEvaluators(evaluatorList);
    });

    fetchEvaluationResults(offset, PAGE_SIZE).then((results) => {
      if (isMounted) {
        setAllData(results);
        setLoading(false);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [page]);

  useEffect(() => {
    setPage(1);
  }, [evaluatorFilter, startDate, endDate]);

  if (loading) return <p>Loading...</p>;

  function setEvaluatorFilter(value: string): void {
    setEvaluatorFilterState(value);
  }

  function setStartDate(value: string): void {
    setStartDateFilterState(value);
  }

  function setEndDate(value: string): void {
    setEndDateFilterState(value);
  }

  function handleSort(key: "score" | "timestamp"): void {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  }

  return (
    <div>
      <h1>See previous evaluation results below </h1>
      <p>Click on one to get more details</p>
      <div className="filters">
        <div>
          <p>Filter by evaluators</p>
          <select onChange={(e) => setEvaluatorFilter(e.target.value)}>
            <option value="">All Evaluators</option>
            {evaluators.map((e) => (
              <option key={e.id} value={e.id}>
                {e.id.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </div>
        <div>
          <p>Select start time</p>
          <input type="date" onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div>
          <p>Select end time</p>
          <input type="date" onChange={(e) => setEndDate(e.target.value)} />
        </div>
      </div>
      <table className="results-table">
        <thead>
          <tr>
            <th className="sort" onClick={() => handleSort("score")}>
              Score
            </th>
            <th>Evaluators</th>
            <th>Status</th>
            <th className="sort" onClick={() => handleSort("timestamp")}>
              Timestamp
            </th>
          </tr>
        </thead>
        <tbody>
          {tableData.map((item) => (
            <tr key={item.id} onClick={() => navigate(`/details/${item.id}`)}>
              <td>{item.score.toFixed(2)}</td>
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
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>
        <span>Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={allData.length < PAGE_SIZE}
        >
          Next
        </button>
      </div>
    </div>
  );
}
