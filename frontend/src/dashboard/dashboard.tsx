import { useEffect, useState, useRef } from 'react';

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
//    const ref = useRef<ChartJS>(null);

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
        console.log("KEY:" + key);
        return {
            label: num.filter(x => x !== null).length + " | " + key,
            data: num,
            fill: false,
            spanGaps: true
        }
    });

    const plotData = {
        labels: filteredData.map(a => dateToFormattedString(a.created_at as Date)),
        datasets: datasets,
    };

    const options = {
            plugins: {
                legend: {
                    title: {
                        display: true,
                        text: "PLACEHOLDER TITLE"
                    }
                }
            }
    }

  return (
    <div>
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
    evaluators: Evaluator[]
}
function Filters({evaluators}: FiltersProps) {
    const today = dayjs();
    const yesterday = today.subtract(1, 'days');

    const [startDate, setStartDate] = useState<Dayjs>(today);
    const [endDate, setEndDate] = useState<Dayjs>(yesterday);

    return (
        <div style={{display: "flex", gap: '2em', padding: '0em 1em 0.5em 1em'}}> 
            <DateTimePicker
                label="Start date"
                value={startDate}
                onChange={(date) => setStartDate(date != null ? date : today)}
                slotProps={{
                  textField: { size: "small" },
                }}
              />
            <DateTimePicker
                label="End date"
                value={endDate}
                onChange={(date) => setEndDate(date != null ? date : yesterday)}
                slotProps={{
                  textField: { size: "small" },
                }}
              />
        </div>
    );
}

export default function Dashboard() {
    const [evaluators, setEvaluators] = useState([]);
    const [data, setData] = useState<AggregatedResultEntity[]>([]);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if(evaluators.length == 0) {
            fetch("http://localhost:8000/evaluators")
                .then(res => res.json())
                .then(json => {
                    setEvaluators(json)
                });

            fetch("http://localhost:8000/results")
                .then(res => res.json())
                .then(json => {
                    json = json as AggregatedResultEntity[];
                    for(var i = 0; i < json.length; i++) {
                        json[i].created_at = new Date(json[i].created_at);
                    }
                    setData(json);
                    setIsLoaded(true);
                });
        } else {
            console.log("Redundant update saved");
        }
    }, [isLoaded]);


//    console.log(evaluators);

    if(!isLoaded) {
        return (
            <div>
                <h1>Welcome to dashboard</h1>
                <Filters evaluators={evaluators}/>
                <h1>Loading results..</h1>
            </div>
        );
    }

    return (
            <div>
                <h1>Welcome to dashboard</h1>
                <Filters evaluators={evaluators}/>
                <EvaluatorGraph data={data} evaluators={evaluators}/>
            </div>
    );
}

//interface FilterEvaluatorProps {
//    evaluators: Evaluator[]
//}
//function FilterEvaluator({evaluators}: FilterEvaluatorProps) {
//    const [isDropDownOpen, setIsDropDownOpen] = useState(false);
//
////    console.log(evaluators);
//    const evaluatorFilters = evaluators.map(e => 
//        <SingleFilterEvaluator key={e.evaluator_id} name={e.evaluator_id} enabledByDefault={false}/>
//   );
//    return (
//        <div className="relative">
//            <button onClick={() => {
//                setIsDropDownOpen(!isDropDownOpen)
//            }}>Evaluators filter</button>
//
//            { isDropDownOpen &&
//                <div>
//                    <SingleFilterEvaluator name="Aggregated Evaluators" enabledByDefault={true}/>
//                    {evaluatorFilters}
//                </div>
//            }
//
//        </div>
//    );
//}
