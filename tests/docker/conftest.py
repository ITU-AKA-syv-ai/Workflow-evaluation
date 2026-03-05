import docker
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.exceptions import ContainerStartException
from testcontainers.core.wait_strategies import LogMessageWaitStrategy


@pytest.fixture(scope="session")
def container():
    try:
        with DockerContainer("fastapi-app").with_exposed_ports(8000).waiting_for(
            LogMessageWaitStrategy("Application startup complete")  # looks for the logs you would normally see in your terminal
        ) as container:
            yield container
    except (ContainerStartException, docker.errors.ImageNotFound):
        pytest.fail("Image 'fastapi-app' not found locally. Run 'docker build -t fastapi-app .' first.")
