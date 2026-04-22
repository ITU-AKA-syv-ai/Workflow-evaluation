import {useEffect, useState} from "react";
import {useNavigate, useParams} from "react-router-dom";

interface EvaluationDetails {
    id: string;
    created_at: string;
    request: any;
    result: ResultDetails;
}

interface ResultDetails {
    weighted_average_score: number;
    is_partial: boolean;
    failure_count: number;
    results: EvaluationResult[];
}

interface EvaluationResult {
    evaluator_id: string;
    passed: boolean;
    normalised_score: number;
    execution_time: number;
    error: string | null;
    reasoning: unknown;
}


export default function EvaluationDetails(){
    const {id} = useParams<{id: string}>();
    const navigate = useNavigate();

    const [data, setData] = useState<EvaluationDetails | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchEvaluation(){
            try {
                // Uses /api proxy to target backend - see vite.config.ts
                const res = await fetch(`/api/results/${id}`)
                console.log(res)
                const json = await res.json();
                console.log(json);
                setData(json);
            } catch (err: any) {
                setError(err.message);
            }
        }

        if (id) {
            fetchEvaluation();
        }
    }, [id]);

    if (error) {
        return (
            <div className="error">
                <p className="text-center">We got an error! - {error}</p>
            </div>
        )
    }

    if (!data) {
        return <div>Loading...</div>;
    }

    // Format date
    const _created_at = new Date (data.created_at);

    // Sum execution time for all evaluators in result
    let total_execution_time = 0;
    for (let i = 0; i < data.result.results.length; i++) {
        total_execution_time += data.result.results[i].execution_time;
    }

    return (
        <div>
            <button onClick={() => navigate("/overview")}>Go Back</button>

            <p>Evaluation id: {data.id}</p>

            <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}}>
                <div style={{borderStyle: 'solid'}}>
                    <p>CREATED: {_created_at.toLocaleString()}</p>
                </div>
                <div style={{borderStyle: 'solid'}}>
                    <p>SCORE: {(data.result.weighted_average_score).toFixed(2)}</p>
                </div>
                <div style={{borderStyle: 'solid'}}>
                    <p>STATUS: {data.result.failure_count} errors</p>
                </div>
                <div style={{borderStyle: 'solid'}}>
                    <p>EXE-TIME: {(total_execution_time/1000).toFixed(2)} s</p>
                </div>
            </div>

            <div style={{display: 'flex', flexDirection: 'row'}}>
                <div>
                    <h1>Request:</h1>
                    <pre>{JSON.stringify(data.request, null, 2)}</pre>
                </div>
                <div>
                    <h1>Result:</h1>
                    <pre>{JSON.stringify(data.result, null, 2)}</pre>
                </div>
            </div>
        </div>
    )
}