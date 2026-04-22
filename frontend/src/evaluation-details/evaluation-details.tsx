import {useEffect, useState} from "react";
import {useNavigate, useParams} from "react-router-dom";

interface EvaluationDetails {
    id: string;
    created_at: string;
    request: any;
    result: any;
}


export default function EvaluationDetails(){
    const {id} = useParams<{id: string}>();
    const navigate = useNavigate();

    const [data, setData] = useState<EvaluationDetails | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchEvaluation(){
            try {
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

    return (
        <div>
            <button onClick={() => navigate("/overview")}>Go Back</button>

            <p>Evaluation id: {data.id}</p>
            <p>Created at: {data.created_at}</p>
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