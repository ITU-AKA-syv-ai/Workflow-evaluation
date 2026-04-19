
export interface DataEntry {
    timestamp: Date; // x-axis
    score: number; // y-axis
}

export interface DataEntries {
    label: string
    data: DataEntry[]
}

export function toDataEntry(json: any): DataEntry {
    const entry = {
        timestamp: new Date(json["created_at"]),
        score: json["result"]["weighted_average_score"]
    };

    return entry;
}


export function dateToFormattedString(d: Date): string {
    return "" + d.getDate() + "/" + d.getMonth() + "/" + d.getFullYear() + " " + d.getHours() + ":" + d.getMinutes();
}

export interface Evaluator {
    evaluator_id: string
}

export function toEvaluator(json: any): Evaluator {
    const evaluator = {
        evaluator_id: json["evaluator_id"]
    }

    return evaluator;
}
