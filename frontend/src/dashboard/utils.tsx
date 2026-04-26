
export function average(data: number[]): number {
    var sum = 0;
    for(var i = 0; i < data.length; i++) {
        sum += data[i];
    }
    return (data.length == 0) ? 0 : (sum / data.length);
}

export function meanDeviation(data: number[], mean: number) {
    const n = data.length;

    var sum = 0;
    for(var i = 0; i < n; i++) {
        const diff = data[i] - mean;
        sum += diff * diff;
    }

    return (n == 0) ? 0 : (sum / n);
}

