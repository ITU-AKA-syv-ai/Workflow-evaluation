from testcontainers.core.container import DockerContainer


def test_python_version(container: DockerContainer) -> None:
    # Verifies the correct base image version was used
    result = container.exec("python --version")
    assert "3.12" in result.output.decode("utf-8")


def test_uv_installed(container: DockerContainer) -> None:
    # Verifies uv was copied from the base image correctly
    result = container.exec("/bin/uv --version")
    assert result.exit_code == 0


def test_fastapi_binary_exists(container: DockerContainer) -> None:
    # Verifies uv sync completed and installed dependencies into the venv
    result = container.exec("/app/.venv/bin/fastapi --version")
    assert result.exit_code == 0


def test_app_directory_exists(container: DockerContainer) -> None:
    # Verifies the application source was copied into the container
    result = container.exec("test -f /app/app/main.py")
    assert result.exit_code == 0
