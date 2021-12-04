from argparse import Namespace
import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup

import task_Ishmametyev_Nikolay_web_spy as lib
from task_Ishmametyev_Nikolay_web_spy import DEFAULT_GITLAB_URL

GITLAB_PRODUCTS_HTML = "gitlab_features.html"
GITLAB_PRODUCTS_EXPECTED_HTML = "gitlab_features_expected.html"
NUMBER_OF_FREE_PRODUCTS_IN_DUMP = 351
NUMBER_OF_PAID_PRODUCTS_IN_DUMP = 218


@pytest.fixture(scope="session")
def load_gitlab_dump_html():
    gitlab_html = open(GITLAB_PRODUCTS_HTML, 'r').read()
    return gitlab_html


@pytest.fixture(scope="session")
def load_gitlab_fresh_dump_html():
    gitlab_fresh_html = open(GITLAB_PRODUCTS_EXPECTED_HTML, 'r').read()
    return gitlab_fresh_html


@pytest.mark.slow
def test_unknown_site():
    unknown_site = "unknown"
    lib.print_number_of_competitor_products(unknown_site)
    assert 1 == 1


@pytest.mark.slow
def test_process_cli_arguments():
    arguments = Namespace(site="unknown")
    lib.process_cli_arguments(arguments)
    assert 1 == 1


@pytest.mark.slow
def test_free_products(load_gitlab_dump_html):
    html = load_gitlab_dump_html
    bs_obj = BeautifulSoup(html, 'html.parser')
    free_products = lib.find_free_products(bs_obj)
    assert NUMBER_OF_FREE_PRODUCTS_IN_DUMP == len(free_products)


@pytest.mark.slow
def test_paid_products(load_gitlab_dump_html):
    html = load_gitlab_dump_html
    bs_obj = BeautifulSoup(html, 'html.parser')
    paid_products = lib.find_paid_products(bs_obj)
    assert NUMBER_OF_PAID_PRODUCTS_IN_DUMP == len(paid_products)


@pytest.mark.slow
@patch("requests.get")
def test_build_bs_object_from_response(mock_with_request, load_gitlab_dump_html):
    mock_with_request.return_value.text = load_gitlab_dump_html
    lib.build_bs_object_from_response(DEFAULT_GITLAB_URL)
    assert 1 == 1


@pytest.mark.slow
@patch("requests.get")
def test_print_number_of_competitor_products(mock_with_request, load_gitlab_dump_html, capsys):
    mock_with_request.return_value.text = load_gitlab_dump_html

    lib.print_number_of_competitor_products("gitlab")
    captures = capsys.readouterr()
    assert "free products:" in captures.out
    assert "enterprise products:" in captures.out


@pytest.mark.integration_test
def test_build_bs_object_from_response_online():
    lib.build_bs_object_from_response(DEFAULT_GITLAB_URL)
    assert 1 == 1


@pytest.mark.integration_test
def test_number_of_products_online(load_gitlab_fresh_dump_html):
    html = load_gitlab_fresh_dump_html
    bs_obj_dump = BeautifulSoup(html, 'html.parser')
    expected_num_free_products = len(lib.find_free_products(bs_obj_dump))
    expected_num_paid_products = len(lib.find_paid_products(bs_obj_dump))

    bs_obj = lib.build_bs_object_from_response(DEFAULT_GITLAB_URL)
    num_free_products = len(lib.find_free_products(bs_obj))
    num_paid_products = len(lib.find_paid_products(bs_obj))

    assert all([
        expected_num_paid_products == num_paid_products,
        expected_num_free_products == num_free_products,
    ]), (
        f"expected free product count is {expected_num_free_products}, "
        f"while you calculated {num_free_products}; "
        f"expected enterprise product count is {expected_num_paid_products}, "
        f"while you calculated {num_paid_products}"
    )
