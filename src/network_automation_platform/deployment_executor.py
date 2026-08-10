from typing import Protocol


class DeploymentExecutionError(RuntimeError):
    pass


class DeploymentExecutor(Protocol):
    def apply_config(
        self,
        hostname: str,
        config: str,
    ) -> None:
        ...