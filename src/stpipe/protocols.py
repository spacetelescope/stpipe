from typing import Protocol, runtime_checkable


@runtime_checkable
class DataModel(Protocol):
    @property
    def crds_observatory(self) -> str:
        ...

    @property
    def get_crds_parameters(self) -> dict[str, any]:
        ...

    def save(self, path, dir_path, *args, **kwargs) -> None:
        ...
