export interface AggregatedResultEntityRaw {
  id?: string;
  created_at?: string;

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
  };
}
export interface AggregatedResultEntity {
  id: string;
  createdAt?: Date;

  request: {
    modelOutput: string;
  };

  result: {
    passed: boolean;
    score: number;
    failureCount: number;
  };
}

export interface AggregatedResultListItem {
  id: string;
  score: number;
  evaluators: string[];
  passed: boolean;
  timestamp?: Date;
}

export function mapAggregatedResultEntity(
  raw: AggregatedResultEntityRaw,
): AggregatedResultEntity {
  return {
    id: raw.id ?? "undefined",
    createdAt: raw.created_at ? new Date(raw.created_at) : undefined,

    request: {
      modelOutput: raw.request.model_output,
    },

    result: {
      passed: raw.result.results?.every((r) => r.passed) ?? false,
      score: raw.result.weighted_average_score,
      failureCount: raw.result.failure_count,
    },
  };
}

export function mapToAggregatedList(
  rawList: AggregatedResultEntityRaw[],
): AggregatedResultListItem[] {
  return rawList.map((raw) => {
    const evaluators = raw.result.results.map((r) =>
      r.evaluator_id.replaceAll("_", " "),
    );

    return {
      id: raw.id ?? "undefined",
      score: raw.result.weighted_average_score,
      evaluators,
      passed: raw.result.results.every((r) => r.passed),
      timestamp: raw.created_at ? new Date(raw.created_at) : undefined,
    };
  });
}

export function mapAggregatedResultList(
  rawList: AggregatedResultEntityRaw[],
): AggregatedResultEntity[] {
  return rawList.map(mapAggregatedResultEntity);
}
