import { useEffect, useState } from 'react';

import 'chart.js/auto';
import { Line, Chart } from "react-chartjs-2";

import type { DataEntry, Evaluator } from './data.js'
import { toDataEntry, dateToFormattedString, toEvaluator } from './data.js'

interface ChartDataProps {
    entryData: DataEntry[]
}

function ChartData({entryData}: ChartDataProps) {
  const data = {
    labels: entryData.map(a => dateToFormattedString(a.timestamp)),
    datasets: [
      {
        label: "Evaluation Requests Weighted Average Scores",
        data: entryData.map(a => a.score),
        fill: false,
        backgroundColor: "rgb(255, 99, 132)",
        borderColor: "rgba(255, 99, 132, 0.2)",
      },
    ],

  };

  return (
    <div>
      <Line data={data} />
    </div>
  );
}

function extractDataForEvaluator(evaluator_id: string, data: object) {

}


function EvaluatorGraph() {
    const [data, setData] = useState([]);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        fetch("/api/results")
            .then(res => res.json())
            .then(json => {

                const dataEntries = json.map(toDataEntry).sort((a: DataEntry, b: DataEntry) => (a.timestamp === b.timestamp) ? 0 : (a.timestamp < b.timestamp ? -1 : 1));

                setData(dataEntries);
                setIsLoaded(true);
            });
    }, []);

    if(!isLoaded) {
        return (
            <div>
                <h1>Loading evaluator results...</h1>
            </div>
        );
    }

    console.log(data);

    const n = data.length;
//    for(let i = 0; i < n; i++) {
//        const results = data[i]["result"]["results"];
//        for(const result of results) {
//            const id = result["evaluator_id"];
//            const score = result["normalised_score"];
//        }
//    }

    
    var avg = 0.0;
    for(const el of data) {
        avg += el.score;
    }

    avg = (n == 0) ? 0.0 : avg / n;

//    avg = Math.floor(avg * 100) / 100.0;

    return (
        <div>
            <ChartData entryData={data}/>

            <div> Average: {avg.toFixed(2)} </div>
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
function FilterEvaluator({evaluators}: FiltersProps) {
    const [isDropDownOpen, setIsDropDownOpen] = useState(false);

    console.log(evaluators);
    const evaluatorFilters = evaluators.map(e => 
        <SingleFilterEvaluator key={e.evaluator_id} name={e.evaluator_id} enabledByDefault={false}/>
   );
    return (
        <div className="relative">
            <button onClick={() => {
                setIsDropDownOpen(!isDropDownOpen)
            }}>Evaluators filter</button>

            { isDropDownOpen &&
                <div>
                    <SingleFilterEvaluator name="Aggregated Evaluators" enabledByDefault={true}/>
                    {evaluatorFilters}
                </div>
            }

        </div>
    );
}

function Filters({evaluators}: FiltersProps) {

    return (
        <div> <FilterEvaluator evaluators={evaluators}/> </div>
    )
}

export default function Dashboard() {
    const [evaluators, setEvaluators] = useState([]);

    useEffect(() => {
        if(evaluators.length == 0) {
            fetch("/api/evaluators")
                .then(res => res.json())
                .then(json => {
                    setEvaluators(json.map(toEvaluator))
                });
        } else {
            console.log("Redundant update saved");
        }
    }, []);

    console.log(evaluators);

    return (
            <div>
                <h1>Welcome to dashboard</h1>
                <Filters evaluators={evaluators}/>

                <EvaluatorGraph />
            </div>
    );
}
