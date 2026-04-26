import { useEffect, useState } from 'react';

import 'chart.js/auto';
import { Line, Bar } from "react-chartjs-2";

import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";

import dayjs from "dayjs";
import { Dayjs } from "dayjs";
import { useInterval } from "../custom_hooks/useInterval.tsx";
import Tabs from "../custom_components/tabs.tsx";

import type { AggregatedResultEntity, Evaluator } from '../dto/dto.tsx'

import { average } from "./utils.tsx"

import "./dashboard.css"

interface ChartProps {
    data: AggregatedResultEntity[]
    evaluators: Evaluator[]
}
function Chart({data, evaluators}: ChartProps) {
    const filteredData = data.filter(a => a.created_at !== undefined);

    // The labels used on the X-axis, i.e. the timestamps 
    const labels = filteredData.map(a => dateToFormattedString(a.created_at as Date));

    // Dataset for the aggregated values
    var avg = average(
        filteredData
            .filter(x => x.result.weighted_average_score !== undefined)
            .map(x => x.result.weighted_average_score as number)
    );
    const aggregatedDataSet = {
        label: `Weighted Score | Aggregated Evaluations: ${filteredData.length} | Average: ${avg.toFixed(2)}`,
        data: filteredData.map(x => x.result.weighted_average_score),
        spanGaps: true // If there's a gap in the data(null value), then we ignore it and draw a line to the next point.
    };

    // Mapping evaluator_id to the list of scores associated with that evaluator
    var dataPerEvaluator: { [id: string]: number[]; } = {};
    for(const evaluator of evaluators) {
        dataPerEvaluator[evaluator.evaluator_id] = Array(labels.length).fill(null);
    }
    for(const index in filteredData) {
        const dataEntry = data[index];
        for(const result of dataEntry.result.results) {
            dataPerEvaluator[result.evaluator_id][index] = result.normalised_score;
        }
    }

    // The list of datasets for each evaluator as well as the dataset for the aggregated evaluators
    // Each dataset contains the scores(Y-values) a label which contains the average score as well as the number of scores(evaluations)
    const datasets = [aggregatedDataSet].concat(
    Object.entries(dataPerEvaluator).map(([key, scores]) => {
        const n = scores.filter(x => x !== null).length;
        if(n == 0) return null;

        const avg = average(scores).toFixed(2);
        return {
            label: `${key} | Evaluations: ${n} | Average: ${avg}`,
            data: scores,
            spanGaps: true // If there's a gap in the data(null value), then we ignore it and draw a line to the next point.
        }
    }).filter(dataset => dataset !== null));

    const plotData = {
        labels: labels,
        datasets: datasets,
    };

    const options = {
        maintainAspectRatio: false,
        scales: {
            y: {
                min: 0.0,
                max: 1.0,
                ticks: {
                    beginAtZero: true,
                    stepSize: 0.1,
                    autoSkip: false
                }
            }
        },
        plugins: {
            legend: {
                title: {
                    display: true,
                    text: "Evaluator scores over time"
                }
            },
            // Force re-colouring when new data is loaded.
            // This is to ensure the plots don't turn grey whenever new data is loaded.
            colors: {
                forceOverride: true
            }
        }
    }

    // There's always going to be at least 1 dataset, namely the aggregated one.
    // However, if there's nothing else besides that, then that dataset will be completely empty.
    if(datasets.length == 1) {
        return (
            <div>
                No data found within the given dates. 
            </div>
        );
    }

    return (
        <div className="graphContainer">
          <Line data={plotData} options={options} className="graph" />
        </div>
    );
}

interface DistributionProps {
    data: AggregatedResultEntity[];
    evaluator: Evaluator;
}
// Distribution graph for a specific evaluator
function Distribution({data, evaluator}: DistributionProps) {
    const groups = [0.2, 0.4, 0.6, 0.8, 1.0];
    const labels = groups.map(x => `<= ${x}`);
    const count = Array(groups.length).fill(0);

    for(const d of data) {
        // The other graph skips these since their X-coordinate is not known
        // We'll also skip them here so that the distribution graph matches the score graph
        if(d.created_at === undefined) continue;

        for(const result of d.result.results) {
            if(result.evaluator_id !== evaluator.evaluator_id) continue;

            const id = groups.findIndex(x => result.normalised_score <= x);
            if(id >= 0) count[id]++;
        }
    }

    const plotData = {
        labels: labels,
        datasets: [{
            label: `Distribution for ${evaluator.evaluator_id}`,
            data: count
        }],
    };

    const options = {
        maintainAspectRatio: false,
        scales: {
            y: {
                ticks: {
                    beginAtZero: true,
                    stepSize: 1
                }
            }
        },
        plugins: {
            // Force re-colouring when new data is loaded.
            // This is to ensure the plots don't turn grey whenever new data is loaded.
            colors: {
                forceOverride: true
            }
        }
    }

    return (
        <div className="graphContainer">
          <Bar data={plotData} options={options} className="graph" />
        </div>
    );
}

// The Score/Time graph along with the Distribution graph
function EvaluatorGraph({data, evaluators}: ChartProps) {

    const distributionTabs = evaluators.map(evaluator => {
        return {label: evaluator.evaluator_id, component: <Distribution data={data} evaluator={evaluator}/>}
    });

    return (
        <div>
        <Chart data={data} evaluators={evaluators} />
        <Tabs tabs={distributionTabs} />
        </div>
    );
}

interface FiltersProps {
    setStartDate: (date: Dayjs) => void;
    setEndDate: (date: Dayjs) => void;
}
// Date filters for results
function Filters({setStartDate, setEndDate}: FiltersProps) {
    const today = dayjs();
    const yesterday = today.subtract(1, 'days');

    return (
        <div style={{display: "flex", gap: '2em', padding: '1em 1em 0.5em 1em'}}> 
            <DateTimePicker
                label="Start date"
                onChange={(date) => setStartDate(date != null ? date : today)}
                slotProps={{
                  textField: { size: "small" },
                }}
              />
            <DateTimePicker
                label="End date"
                onChange={(date) => setEndDate(date != null ? date : yesterday)}
                slotProps={{
                  textField: { size: "small" },
                }}
              />
        </div>
    );
}

// Primary dashboard with date filters, score over time graph and score distribution bar graph
export default function Dashboard() {
    const fetchLimitSize = 50;

    const today = dayjs();
    const yesterday = today.subtract(1, 'days');
    const [startDate, setStartDate] = useState<Dayjs>(yesterday);
    const [endDate, setEndDate] = useState<Dayjs>(today);

    const [evaluators, setEvaluators] = useState<Evaluator[]>([]);
    const [data, setData] = useState<AggregatedResultEntity[]>([]);
    const [isLoaded, setIsLoaded] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const updateData = (offset: number, limit: number) => {
        var moreToFetch = true;
        // There's a limit to how many results we can get out from the API at once.
        // If we're requesting a lot of data, then we might have to perform the rquests in several batches.
        while(moreToFetch) {
            moreToFetch = false;
            fetch(`http://localhost:8000/results?ascending=true&limit=${limit}&offset=${offset}&start_date=${startDate.toJSON()}&end_date=${endDate.toJSON()}`)
                .then(res => res.json())
                .then(json => {
                    for(var i = 0; i < json.length; i++) {
                        json[i].created_at = new Date(json[i].created_at);
                    }

                    json = json as AggregatedResultEntity[];

                    // If we're using an offset, then that implies we're loading additional data
                    // which comes after the data we've already loaded.
                     if(offset > 0) {
                         setData(data.concat(json));
                     } else {
                         setData(json);
                     }
                    setIsLoaded(true);
                    setError(null);

                    if(json.length == limit) {
                        moreToFetch = true;
                        offset += json.length;
                    }
                })
                .catch(err => setError(err.message))
        }
    }

    useInterval(() => {
        updateData(data.length, fetchLimitSize);
    }, 60000);

    useEffect(() => {
        if(evaluators.length == 0) {
            fetch("http://localhost:8000/evaluators")
                .then(res => res.json())
                .then(json => {
                    setEvaluators(json as Evaluator[])
                }).catch((err) => setError(err.message));
        }
        updateData(0, fetchLimitSize);
    }, [startDate, endDate]);

    if(error != null) {
        return (
                <div>
                    <Filters setStartDate={setStartDate} setEndDate={setEndDate}/>
                    <p>{error}</p>
                </div>
        );
    }

    if(!isLoaded) {
        return (
            <div>
                <Filters setStartDate={setStartDate} setEndDate={setEndDate}/>
                <h1>Loading results..</h1>
            </div>
        );
    }

    if(data.length == 0) {
        return (
            <div>
                <Filters setStartDate={setStartDate} setEndDate={setEndDate}/>
                <h1>No results in given time window</h1>
            </div>
        );
    }

    return (
            <div>
                <Filters setStartDate={setStartDate} setEndDate={setEndDate}/>
                <EvaluatorGraph data={data} evaluators={evaluators}/>
            </div>
    );
}

function dateToFormattedString(d: Date): string {
    return "" + d.getDate() + "/" + d.getMonth() + "/" + d.getFullYear() + " " + d.getHours() + ":" + d.getMinutes();
}
