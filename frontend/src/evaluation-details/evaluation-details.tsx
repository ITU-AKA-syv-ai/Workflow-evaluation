import {useEffect, useState} from "react";
import {useNavigate, useParams} from "react-router-dom";
import "../styles/styles.css"

interface EvaluationDetails {
    id: string;
    created_at: string;
    request: RequestDetails;
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

interface RequestDetails {
    model_output: string;
    configs: EvaluationRequest[];
}

interface EvaluationRequest {
    evaluator_id: string;
    weight: number;
    threshold: number | null;
    config: unknown;
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

                if (res.status == 404) {
                    throw new Error("Could not find evaluation. Try a different id")
                }

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
                <p className="text-center" style={{color: 'red'}}>{error}</p>
            </div>
        )
    }

    if (!data) {
        return <div>Loading...</div>;
    }

    // Format date
    const _created_at = new Date (data.created_at).toLocaleString("en-GB");


    // Sum execution time for all evaluators in result
    let total_execution_time = 0;
    for (let i = 0; i < data.result.results.length; i++) {
        total_execution_time += data.result.results[i].execution_time;
    }

return (
    <div className="page-container">

        <h1 className="large-header">Evaluation Details</h1>

        <br/>

        <button className="back-button" onClick={() => navigate("/overview")}>
            ← Back
        </button>
        <div className="summary-card">
            <p><strong>Evaluation ID:</strong> {data.id}</p>
        </div>

        <br/>

        <div className="summary-container">
            <div className="summary-card">
                <strong>CREATED: </strong>{_created_at.toLocaleString()}
            </div>
            <div className="summary-card">
                <strong>SCORE: </strong>{(data.result.weighted_average_score).toFixed(2)}
            </div>
            <div className="summary-card">
                <strong>STATUS: </strong>{data.result.failure_count} errors
            </div>
            <div className="summary-card">
                <strong>EXE-TIME: </strong>{(total_execution_time/1000).toFixed(2)} s
            </div>
        </div>

        <div className="section">
            <h3>What AI output was evaluated?</h3>
            <p>{data.request.model_output}</p>
        </div>

        <div className="section">
            <div className="section-title">Request</div>
            <div className="section-divider" />
            <div className="card-container">
                {data.request.configs.map((r, i) => (
                    <div className="card" key={i}>
                        <p><strong>Evaluator:</strong> {r.evaluator_id}</p>
                        <p><strong>Weight:</strong> {r.weight}</p>

                        {r.threshold !== null && (
                            <p><strong>Pass threshold:</strong> {r.threshold}</p>
                        )}

                        <h3>Config:</h3>
                        <div className="json-block">
                            {JSON.stringify(r.config, null, 2)}
                        </div>
                    </div>
                ))}
            </div>
        </div>

        <div className="section">
            <div className="section-title">Result</div>
            <div className="section-divider" />
            <div className="card-container">
                {data.result.results.map((r, i) => (
                    <div className="card" key={i}>
                        <p><strong>Evaluator:</strong> {r.evaluator_id}</p>

                        <p className={r.passed ? "passed" : "failed"}>
                            {r.passed ? "Passed" : "Failed"}
                        </p>

                        <p><strong>Score:</strong> {(r.normalised_score).toFixed(2)}</p>

                        <h3>Reasoning:</h3>
                        <div className="json-block">
                            {JSON.stringify(r.reasoning, null, 2)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    </div>
)}