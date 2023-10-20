from collections.abc import Sequence

from stpipe.container import AbstractModelContainer


class BadContainer(Sequence):
    def __getitem__(self):
        pass

    def __len__(self):
        pass

    def save(self, path, save_model_func):
        pass

    @staticmethod
    def read_asn(filepath):
        pass

    def from_asn(self, asn_data, asn_file_path=None):
        pass


class GoodContainer(BadContainer):
    @property
    def crds_observatory(self):
        return ""


def test_good_container():
    assert issubclass(GoodContainer, AbstractModelContainer)
    gc = GoodContainer()
    assert isinstance(gc, AbstractModelContainer)


def test_bad_container():
    assert not issubclass(BadContainer, AbstractModelContainer)
    bc = BadContainer()
    assert not isinstance(bc, AbstractModelContainer)
