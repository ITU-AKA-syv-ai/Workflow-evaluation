from testcontainers.core.container import DockerContainer
import requests


def test_docker_returns_200(container):

        host = container.get_container_host_ip() #usually local host
        port = container.get_exposed_port(8000) #testcontainer lets docker assign a random host port and it is then retrieved

        assert (requests.get(f"http://{host}:{port}/")).status_code == 200
