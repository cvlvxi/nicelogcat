import pathlib
import pytest

data = pathlib.Path(__file__).parent / "testdata.log"


@pytest.fixture()
def logstream():
    fh = open(data, "rb")
    yield fh
    fh.close
