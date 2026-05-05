// DTOS:
// Represents the results of each individual strategy
export interface EvaluationResult {
    evaluator_id: string;
    passed: boolean;
    normalised_score: number;
    execution_time: number;
    error: string | null;
    reasoning: unknown;
}

// Represents top-level information about the request
export interface EvaluationRequest {
    model_output: string;
    configs: EvaluationRequest[];
}

// Represents the request for each individual strategy
export interface EvaluationRequest {
    evaluator_id: string;
    weight: number;
    threshold: number | null;
    config: unknown;
}

// Represents the aggregated results of the evaluation
export interface EvaluationResponse {
    weighted_average_score?: number;
    results: EvaluationResult[];
    is_partial: boolean;
    failure_count: number;
}
 
// Represents top-level information about the evaluation
export interface AggregatedResultEntity {
    request: EvaluationRequest;
    result: EvaluationResponse;
    id?: any;
    created_at?: Date;
}

export interface Evaluator {
    evaluator_id: string;
    description: string;
    config_schema: [string, any];
}
