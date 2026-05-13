# Workflow Evaluation

This application is a backend service for evaluating AI-generated outputs using multiple evaluation strategies, accessed through a REST API.

The system supports both synchronous and asynchronous evaluation workflows,
allowing evaluations to either return immediately or be processed in the background.

The application is designed to be extensible, making it possible to add new evaluators, evaluation strategies, and providers.

Currently supported evaluator types include:

- **LLM as Judge.** Uses an LLM to assess the quality of AI output based on subjective criteria like clarity, correctness, and completeness.

- **Rule-Based Evaluator.** Checks AI outputs against simple, predefined rules.
These rules can enforce things like required keywords, allowed formats, or matching patterns.

- **Cosine Similarity Evaluator.** Measures how semantically similar an AI generated output is to a given reference text.

- **ROUGE Evaluator.** Measures how much overlap there is between an AI generated output and a reference text.

You can find a comprehensive example sheet for all evaluators [here](docs/evaluation-examples.md).


# Getting Started

## Prerequisites

This application requires [Docker](https://www.docker.com/get-started/). Make sure it is installed and running before proceeding.

Docker can be installed either as a CLI (Command Line Interface) or as the Docker Desktop application.

Either will work but if you're using Docker CLI, you'll also need to install the [Docker Compose plugin](https://docs.docker.com/compose/install).

## 1. Download zip or Clone the Repository

Either download the project as a zip file from [here](https://github.com/ITU-AKA-syv-ai/Workflow-evaluation/archive/refs/heads/main.zip) and unzip it.

Or clone the repository using [git](https://git-scm.com/):
```
git clone https://github.com/ITU-AKA-syv-ai/Workflow-evaluation
```

Then open a terminal window on your computer and navigate to the project folder. E.g. `cd Workflow-evaluation` or `cd Workflow-evaluation-main`


## 2. Setup Environment Variables

In the root of the project directory, you'll find a file called `.env.example`.
Create a copy of that file in the same folder and rename the copy `.env`.

This file contains values and settings required to run the application.

Open `.env` in a text editor i.e. Notepad for Windows or TextEdit for Mac.

Then, fill out all the variables in the file. You can refer to [this](docs/development.md#environment-variables) table for more information.
When running the application locally for development, set the ENVIRONMENT variable to `dev` at the very top of the `.env` file.


## 3. Run the App Using Docker

To start the app, use the Docker compose command below in the root of the project `\Workflow-evaluation` / `\Workflow-evaluation-main`

```
docker compose up
```

That's it! You should see the app starting up. It will take a minute or so before the app is ready to be used.


## Using the Application

*Note: `<HOST>` means the IP address of the machine the application is running on.
If you are running the app locally and accessing it on the same device, your `<HOST>` will simply be `localhost`.*

Once the app has started you can view the status of the application by typing the following into your web browser of choice:

`<HOST>:8000/status`

To use the application i.e. send and view evaluations, you can use the docs page provided by Swagger UI:

`<HOST>:8000/docs`

If you want to browse an overview, dashboard and details about previous evaluations, you can do so here:

`<HOST>:5173`

### Swagger UI docs page

The `/docs` page is an excellent tool to help you get started using the application.
There, you will find an overview and documentation of all API endpoints,
and you can experiment with your own evaluation requests and results.

If you have been following the guide and are running the app locally in a `dev` environment,
you need to get authorised before you can send evaluations.

1. Open `http://localhost:8000/docs`.
2. Go to the `/dev/token` endpoint.
3. Click "Try it out" and "Execute"
4. In the response body, copy the value of `"access_token"` to your clipboard.
5. At the top of the page, click on the "Authorize" button and paste the value you just copied. 

Now you should be able to send and browse evaluations through Swagger directly.

*Note: If the token is rejected as invalid or the frontend doesn't load, try clearing your browser's
cache for localhost.*


### Calling the API directly

It is generally recommended that you use the Swagger `/docs` page and [evaluation-examples.md](docs/evaluation-examples.md) to familiarise yourself with the API,
as shown in the previous section.
A direct call to the application from a terminal might look something like this:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/evaluations' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your-token> \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "model_output": "hello",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1.0,
        "config": {
          "rules": [
            {
              "name": "format",
              "kind": "max_length",
              "max_length": 10,
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]'
```

# System Architecture

The folder structure of the application is as follows:

```
Workflow-evaluation/
├─ backend/                 # Source code for the backend
│  ├─ app/
│  │  ├─ main.py            # Router setup
│  │  ├─ api/               # Handlers for each endpoint
│  │  ├─ core/              # The core app logic
│  │  │  ├─ services/       # Services which the endpoint handlers call
│  │  │  ├─ models/         # Data models which the services use
│  │  │  ├─ evaluators/     # Logic for evaluators
│  │  │  ├─ providers/      # LLM provider classes
│  │  ├─ config/            # Config files
│  ├─ tests/
├─ frontend/
│  ├─ src/                  # Source code for the frontend
```

## Architecture Diagrams

### Component diagram
![Component Diagram](docs/diagrams/abstractComponent.svg)

### Class diagram
![Overview of architecture](docs/diagrams/component.svg)

### Data Flow
![Data Flow Diagram](docs/diagrams/DataFlow.svg)

## Backend Development
Please see [./backend/README.md](docs/backend.md)

## Frontend Development
Please see [./frontend/README.md](docs/frontend.md)

## Development
Please see [./development.md](docs/development.md)

## Deployment
Currently, there is no guide to deploying the application.

## License
Licensed under the terms of the MIT license. Please see [./LICENSE](./LICENSE).
