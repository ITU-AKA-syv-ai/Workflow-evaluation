import { useEffect, useState } from 'react';

import 'chart.js/auto';
import { Line } from "react-chartjs-2";

import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";

import dayjs from "dayjs";
import { Dayjs } from "dayjs";

import type { AggregatedResultEntity, Evaluator } from '../dto/dto.tsx'
import { dateToFormattedString } from './data.tsx'

interface ChartProps {
    data: AggregatedResultEntity[]
    evaluators: Evaluator[]
}
function Chart({data, evaluators}: ChartProps) {
    const filteredData = data.filter(a => a.created_at !== undefined);
    const labels = filteredData.map(a => dateToFormattedString(a.created_at as Date));

    var dataPerEvaluator: { [id: string]: number[]; } = {};

    for(const evaluator of evaluators) {
        dataPerEvaluator[evaluator.evaluator_id] = Array(labels.length).fill(null);
    }

    for(const index in data) {
        const dataEntry = data[index];
        for(const result of dataEntry.result.results) {
            dataPerEvaluator[result.evaluator_id][index] = result.normalised_score;
        }
    }

    const datasets = 
    Object.entries(dataPerEvaluator).map(([key, num]) => {
        const n = num.filter(x => x !== null).length;
        if(n == 0) return null;

        const sum = num.filter(x => x !== null).reduce(((a, b) => a + b), 0);
        const avg = (n !== 0) ? (sum / n).toFixed(2) : 0;
        return {
            label: "Average: " + avg + " | " + num.filter(x => x !== null).length + " | " + key,
            data: num,
            fill: false,
            spanGaps: true
        }
    }).filter(dataset => dataset !== null);

    if(datasets.length == 0) {
        return (
            <div>
                No data found within the given dates. 
            </div>
        );
    }

    const plotData = {
        labels: filteredData.map(a => dateToFormattedString(a.created_at as Date)),
        datasets: datasets,
    };

    const options = {
            plugins: {
                legend: {
                    title: {
                        display: true,
                        text: "Evaluator scores over time"
                    }
                },
                colors: {
                    forceOverride: true
                }
            }
    }

    return (
    <div style={{position: "relative", width: "70em", height: "30em"}}>
      <Line data={plotData} options={options} />
    </div>
  );
}

function EvaluatorGraph({data, evaluators}: ChartProps) {
    const n = data.length;
    
    var avg = 0.0;
    for(const el of data) {
        if(el.result.weighted_average_score !== undefined)
            avg += el.result.weighted_average_score;
    }

    avg = (n == 0) ? 0.0 : avg / n;

    return (
        <div>
        <Chart data={data} evaluators={evaluators} />

        <span> Average: {avg.toFixed(2)} </span>
        </div>
    );
}


interface SingleFilterEvaluatorProps {
    name: string
    enabledByDefault: boolean
}
function SingleFilterEvaluator({name, enabledByDefault}: SingleFilterEvaluatorProps) {
    return (
        <label>
        {name}: <input type="checkbox" defaultChecked={enabledByDefault} />
        </label>
    );
}


interface FiltersProps {
    setStartDate: (date: Dayjs) => void;
    setEndDate: (date: Dayjs) => void;
}
function Filters({setStartDate, setEndDate}: FiltersProps) {
    const today = dayjs();
    const yesterday = today.subtract(1, 'days');

    return (
        <div style={{display: "flex", gap: '2em', padding: '1em 1em 0.5em 1em'}}> 
            <DateTimePicker
                label="Start date"
                value={today}
                onChange={(date) => setStartDate(date != null ? date : today)}
                slotProps={{
                  textField: { size: "small" },
                }}
              />
            <DateTimePicker
                label="End date"
                value={yesterday}
                onChange={(date) => setEndDate(date != null ? date : yesterday)}
                slotProps={{
                  textField: { size: "small" },
                }}
              />
        </div>
    );
}

export default function Dashboard() {
    const today = dayjs();
    const yesterday = today.subtract(1, 'days');
    const [startDate, setStartDate] = useState<Dayjs>(today);
    const [endDate, setEndDate] = useState<Dayjs>(yesterday);

    const [evaluators, setEvaluators] = useState<Evaluator[]>([]);
    const [data, setData] = useState<AggregatedResultEntity[]>([]);
    const [isLoaded, setIsLoaded] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if(evaluators.length == 0) {
            fetch("http://localhost:8000/evaluators")
                .then(res => res.json())
                .then(json => {
                    setEvaluators(json)
                });
        }

        fetch(`http://localhost:8000/results?limit=50&ascending=true&start_date=${startDate.toJSON()}&end_date=${endDate.toJSON()}`)
            .then(res => res.json())
            .then(json => {
                json = json as AggregatedResultEntity[];
                for(var i = 0; i < json.length; i++) {
                    json[i].created_at = new Date(json[i].created_at);
                }
                setData(json);
                setIsLoaded(true);
                setError(null);
            })
            .catch(err => setError(err))
    }, [startDate, endDate]);

    if(!isLoaded) {
        return (
            <div>
                <Filters setStartDate={setStartDate} setEndDate={setEndDate}/>
                <h1>Loading results..</h1>
            </div>
        );
    }

    if(error != null) {
        return (
                <div>
                    <Filters setStartDate={setStartDate} setEndDate={setEndDate}/>
                    <h1>{error}</h1>
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
