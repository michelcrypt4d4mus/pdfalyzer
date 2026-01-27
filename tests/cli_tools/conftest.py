import pytest

from ..conftest import FIXTURES_DIR


@pytest.fixture(scope="session")
def multipage_pdf_path():
    return FIXTURES_DIR.joinpath('The Consul General at Berlin to FDR underecretary of State June 1933.pdf')
