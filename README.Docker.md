### Building and running the application

First, make sure Docker is installed and running. 

To build the Docker image, run: `docker build -t fastapi-app .`

To run the containerized application, run: `docker run -p 8000:8000 fastapi-app`

The IP and port will be printed in the terminal, but should by default be http://0.0.0.0:8000. (subject to change)

### Deploying the application to the cloud

Not implemented yet...

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)
* [Using uv with FastAPI](https://docs.astral.sh/uv/guides/integration/fastapi/)