from testcontainers.core.container import DockerContainer
import requests
from testcontainers.core.wait_strategies import LogMessageWaitStrategy


def test_docker_returns_200():
    with DockerContainer("fastapi-app").with_exposed_ports(8000).waiting_for(
            LogMessageWaitStrategy("Application startup complete")) as container: #looks for the logs you would normally see in your terminal

        host = container.get_container_host_ip() #usually local host
        port = container.get_exposed_port(8000) #testcontainer lets docker assign a random host port and it is then retrieved

        assert (requests.get(f"http://{host}:{port}/")).status_code == 200
