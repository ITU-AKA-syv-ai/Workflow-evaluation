# Getting Started

## Prerequisites

This application requires [Docker](https://www.docker.com/get-started/). Make sure it is installed and running before proceeding.

Docker can be installed either as a CLI (Command Line Interface) or as the Docker Desktop application.

Either will work but if you're using Docker CLI, you'll also need to install the [Docker Compose plugin](https://docs.docker.com/compose/install).

## 1. Download zip or clone the repository

Either download the project as a zip file from [here](https://github.com/ITU-AKA-syv-ai/Workflow-evaluation/archive/refs/heads/main.zip) and unzip it.

Or clone the repository using [git](https://git-scm.com/):
```
git clone https://github.com/ITU-AKA-syv-ai/Workflow-evaluation
```

Then open a terminal window on your computer and navigate to the project folder. E.g.

```
cd Workflow-evaluation
```


## 2. Setup environment variables

In the root of the project directory, you'll find a file called `.env.example`.
Create a copy of that file in the same folder and rename the copy `.env`.

This file contains values and settings required to run the application.

Open `.env` in a text editor i.e. Notepad for Windows or TextEdit for Mac.

Then, fill out all the variables in the file. You can refer to [this](development.md#environment-variables) table for more information.


## 3. Run the app using Docker

To start the app, use the Docker compose command below in the root of the project `\Workflow-evaluation`.

```
docker compose up
```

That's it! You should see the app starting up. It will take a minute or so before the app is ready to be used.


## Using the application

*Note: `<HOST>` means the IP address of the machine the application is running on.
If you are running the app locally and accessing it on the same device, your `<HOST>` will simply be `localhost`.*

Once the app has started you can view the status of the application by typing the following into your web browser of choice:

`<HOST>:8000/status`

To use the application i.e. send and view evaluations, you can use the docs page provided by Swagger UI:

`<HOST>:8000/docs`

If you want to browse an overview, dashboard and details about previous evaluations, you can do so here:

`<HOST>:5173`