# Getting Started

## Prerequisites

This application requires [Docker](https://www.docker.com/get-started/). Install it and ensure it is running.

If you're using Docker CLI and not Docker Desktop, then you'll also need to install the [Docker Compose plugin](https://docs.docker.com/compose/install).

### 1. Clone the repository

Either [download](https://github.com/ITU-AKA-syv-ai/Workflow-evaluation/archive/refs/heads/main.zip) the project as a zip file, unzip it and navigate inside the directory.
Or clone the repository using [git](https://git-scm.com/) and navigate inside the directory.

```
git clone https://github.com/ITU-AKA-syv-ai/Workflow-evaluation && cd Workflow-evaluation
```

### 2. Setup environment variables

Make a copy of `.env.example` and name it `.env`.
Open `.env` within a text editor.
Setup all environment varaibles according to your use case. Refer to the [this](development.md) table for more information.


### 3. Run the app using Docker

The app can be started by using docker compose.

```
docker compose up
```

