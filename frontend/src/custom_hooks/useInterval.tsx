
import { useEffect, useEffectEvent } from 'react';

// https://react.dev/reference/react/useEffectEvent#using-effect-events-in-custom-hooks
export function useInterval(callback: () => void, delay: number) {
    const onTick = useEffectEvent(callback);

    useEffect(() => {
        if (delay === null) {
            return;
        }
        const id = setInterval(() => {
            onTick();
        }, delay);
        return () => clearInterval(id);
    }, [delay]);
}
