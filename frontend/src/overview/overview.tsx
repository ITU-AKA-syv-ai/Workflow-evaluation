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
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Dayjs } from "dayjs";
import {
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
  colors,
} from "@mui/material";

const PAGE_SIZE = 10;

async function fetchEvaluationResults(
  offset: number,
  limit: number,
): Promise<AggregatedResultListItem[]> {
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
  const [evaluatorFilter, setEvaluatorFilter] = useState<string[]>([]);
  const [startDate, setStartDate] = useState<Dayjs | null>(null);
  const [endDate, setEndDate] = useState<Dayjs | null>(null);
  const [sortKey, setSortKey] = useState<"score" | "timestamp" | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const tableData = useMemo(() => {
    if (!allData || allData.length === 0) return [];
    //filration
    let filtered = allData.filter((item) => {
      if (
        evaluatorFilter.length > 0 &&
        !evaluatorFilter.some((filter) =>
          item.evaluators.includes(filter.replaceAll("_", " ")),
        )
      ) {
        return false;
      }

      const ts = item.timestamp ? new Date(item.timestamp) : null;

      if (startDate) {
        const sd = startDate.startOf("day").toDate();
        if (!ts || ts < sd) return false;
      }

      if (endDate) {
        const ed = endDate.endOf("day").toDate();
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
          <Select
            multiple
            displayEmpty
            value={evaluatorFilter}
            onChange={(e) => {
              const value = e.target.value;
              setEvaluatorFilter(
                typeof value === "string" ? value.split(",") : value,
              );
            }}
            input={<OutlinedInput />}
            renderValue={(selected) => {
              if (selected.length === 0) {
                return <em>Select evaluators</em>;
              }
              return selected.map((val) => val.replaceAll("_", " ")).join(", ");
            }}
          >
            <MenuItem disabled value="">
              <em>All Evaluators</em>
            </MenuItem>

            {evaluators.map((e) => (
              <MenuItem key={e.id} value={e.id}>
                <Checkbox checked={evaluatorFilter.includes(e.id)} />
                <ListItemText primary={e.id.replaceAll("_", " ")} />
              </MenuItem>
            ))}
          </Select>
        </div>
        <div>
          <p>Select start time</p>
          <DatePicker
            label="Start date"
            value={startDate}
            onChange={(newValue) => setStartDate(newValue)}
            format="DD/MM/YYYY"
            slotProps={{
              textField: { size: "small" },
            }}
          />
        </div>
        <div>
          <p>Select end time</p>
          <DatePicker
            label="End date"
            value={endDate}
            onChange={(newValue) => setEndDate(newValue)}
            format="DD/MM/YYYY"
            slotProps={{
              textField: { size: "small" },
            }}
          />
        </div>
      </div>
      <table className="results-table">
        <thead>
          <tr>
            <th
              className="sort"
              onClick={() => handleSort("score")}
              role="button"
              aria-sort={
                sortKey === "score"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : "none"
              }
              title={
                sortKey === "score"
                  ? `Sorted by score (${sortDirection}) - click to toggle`
                  : "Click to sort by score"
              }
            >
              <span
                style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
              >
                Score
                <span
                  aria-hidden="true"
                  className={`sort-icon ${sortKey === "score" ? sortDirection : ""}`}
                >
                  {sortKey === "score"
                    ? sortDirection === "asc"
                      ? "▲"
                      : "▼"
                    : "⇅"}
                </span>
              </span>
            </th>
            <th>Evaluators</th>
            <th>Status</th>
            <th
              className="sort"
              onClick={() => handleSort("timestamp")}
              role="button"
              aria-sort={
                sortKey === "timestamp"
                  ? sortDirection === "asc"
                    ? "ascending"
                    : "descending"
                  : "none"
              }
              title={
                sortKey === "timestamp"
                  ? `Sorted by score (${sortDirection}) - click to toggle`
                  : "Click to sort by score"
              }
            >
              <span
                style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
              >
                Timestamp
                <span
                  aria-hidden="true"
                  className={`sort-icon ${sortKey === "timestamp" ? sortDirection : ""}`}
                >
                  {sortKey === "timestamp"
                    ? sortDirection === "asc"
                      ? "▲"
                      : "▼"
                    : "⇅"}
                </span>
              </span>
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
