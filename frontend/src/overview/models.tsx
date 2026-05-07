export const EvaluationStatus = {
  PENDING: "PENDING",
  RECEIVED: "RECEIVED",
  RUNNING: "RUNNING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
} as const;

export type EvaluationStatus =
  (typeof EvaluationStatus)[keyof typeof EvaluationStatus];

export interface AggregatedResultEntityRaw {
  id?: string;
  created_at?: string;
  updated_at?: string;
  status?: string;

  request: {
    model_output: string;
    configs: unknown[]; // refine later if needed
  };

  result: {
    weighted_average_score: number;
    is_partial: boolean;
    failure_count: number;

    results: {
      evaluator_id: string;
      passed: boolean;
      reasoning: string;
    }[];
  } | null;
}

export interface AggregatedResultListItem {
  id: string;
  score: number;
  evaluators: string[];
  passed: boolean;
  timestamp?: Date;
  job_status: EvaluationStatus;
}

export interface EvaluatorsRaw {
  evaluator_id: string;
}

export interface Evaluators {
  id: string;
}

export function mapToAggregatedList(
  rawList: AggregatedResultEntityRaw[],
): AggregatedResultListItem[] {
  return rawList.map((raw) => {
    const evaluators =
      raw.result?.results.map((r) => r.evaluator_id.replaceAll("_", " ")) ?? [];
    return {
      id: raw.id ?? "undefined",
      score: raw.result?.weighted_average_score ?? 0,
      evaluators,
      passed: raw.result?.results.every((r) => r.passed) ?? false,
      timestamp: raw.created_at ? new Date(raw.created_at) : undefined,
      job_status: raw.status as EvaluationStatus,
    };
  });
}

export function mapEvaluators(rawList: EvaluatorsRaw[]): Evaluators[] {
  return rawList.map((raw) => ({
    id: raw.evaluator_id,
  }));
}
