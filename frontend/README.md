# Frontend

The frontend is built with `Vite`, `React` and `TypeScript`.

## Quick Start
To install dependencies please run
```
bun install

```
To then run the application please run
```
bun run dev --hot
```
It is easier to just run the frontend with the above command to modify the frontend with hot-reloading, but running the docker container with [../compose.override.yaml](../compose.override.yaml) also has hot-reloading enabled. In production the frontend is served with nginx.
