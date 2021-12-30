import pytest
from unittest.mock import patch
import requests

from task_Ishmametyev_Nikolay_asset_web_service import (
    app, extract_cbr_daily_data_obj,
    parse_cbr_currency_base_daily,parse_cbr_key_indicators,
    DAILY_CURRENCY_TABLE_PARAMS, URL_CBR_DAILY, URL_CBR_KEY_INDICATORS,
    Asset, Portfolio
)

ASSET_RUB_EXAMPLE_STR = "RUB asset_rub 1000 0.2"
ASSET_USD_EXAMPLE_STR = "USD asset_usd 1000 0.05"
CBR_DAILY_DUMP = "cbr_currency_base_daily.html"
CBR_KEY_INDICATORS_DUMP = "cbr_key_indicators.html"


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_cbr_daily_column_index():
    EXPECTED_DAILY_COL_NUMBER = 5
    html_data = requests.get(URL_CBR_DAILY).text
    table_data = extract_cbr_daily_data_obj(html_data)

    current_idx = {
        col.find(text=True).lower(): idx for idx, col in enumerate(table_data[0].find_all("th"))
    }
    assert EXPECTED_DAILY_COL_NUMBER == len(current_idx)

    for key, idx in DAILY_CURRENCY_TABLE_PARAMS["column_idx"].items():
        assert idx == current_idx[key]


def test_parse_cbr_daily():
    html_data = requests.get(URL_CBR_DAILY).text
    rates = parse_cbr_currency_base_daily(html_data)
    assert "USD" not in rates
    assert "CHF" in rates


def test_parse_key_indicators():
    html_data = requests.get(URL_CBR_KEY_INDICATORS).text
    rates = parse_cbr_key_indicators(html_data)
    assert "Au" in rates


# def test_parse_cbr_daily_dump():
#     html_data = open(CBR_DAILY_DUMP).read()
#     rates = parse_cbr_currency_base_daily(html_data)
#     assert "USD" not in rates
#     assert "CHF" in rates
#
#
# def test_parse_key_indicators_dump():
#     html_data = open(CBR_KEY_INDICATORS_DUMP).read()
#     rates = parse_cbr_key_indicators(html_data)
#     assert "Au" in rates


def test_cbr_daily_endpoint(client):
    response = client.get("/cbr/daily")
    assert response.is_json


def test_cbr_key_indicators(client):
    response = client.get("/cbr/key_indicators")
    assert response.is_json


@patch("requests.get")
def test_unavailable_cbr(mock_get, client):
    mock_get.side_effect = [requests.exceptions.ConnectionError]

    response = client.get("/cbr/key_indicators", follow_redirects=True)
    assert response.status_code >= 500


def test_calculate_rub_revenue(client):
    years = 3
    rates = {"USD": 72.3}
    asset = Asset.build_from_str(ASSET_RUB_EXAMPLE_STR)
    expected_revenue = asset.capital * ((1.0 + asset.interest) ** years - 1.0)

    currency_rate = rates.get(asset.char_code) or 1
    calculated_revenue = asset.calculate_revenue(years, currency_rate)
    pytest.approx(expected_revenue, calculated_revenue)


def test_calculate_usd_revenue(client):
    years = 3
    rates = {"USD": 72.3}
    asset = Asset.build_from_str(ASSET_USD_EXAMPLE_STR)
    expected_revenue = asset.capital * ((1.0 + asset.interest) ** years - 1.0) * rates["USD"]

    currency_rate = rates.get(asset.char_code) or 1
    calculated_revenue = asset.calculate_revenue(years, currency_rate)
    pytest.approx(expected_revenue, calculated_revenue)


def test_portfolio_add_duplicate():
    portfolio = Portfolio()
    asset = Asset.build_from_str(ASSET_USD_EXAMPLE_STR)
    asset_duplicate = Asset.build_from_str(ASSET_USD_EXAMPLE_STR)
    portfolio.add(asset)
    with pytest.raises(ValueError):
        portfolio.add(asset_duplicate)


def test_portfolio_calculate_revenue():
    portfolio = Portfolio()
    asset_rub = Asset.build_from_str(ASSET_RUB_EXAMPLE_STR)
    asset_usd = Asset.build_from_str(ASSET_USD_EXAMPLE_STR)
    portfolio.add(asset_rub)
    portfolio.add(asset_usd)

    years = 3
    rates = {"USD": 72.3}
    expected_revenue_rub = asset_rub.capital * (
            (1.0 + asset_rub.interest) ** years - 1.0
    )
    expected_revenue_usd = asset_usd.capital * (
            (1.0 + asset_usd.interest) ** years - 1.0
    ) * rates["USD"]
    expected_revenue = expected_revenue_rub + expected_revenue_usd
    calculated_revenue = portfolio.calculate_revenue(years, rates)
    pytest.approx(expected_revenue, calculated_revenue)


def test_add_asset(client):
    char_code = "USD"
    name = "asset"
    capital = "100"
    interest = "0.5"
    response = client.get(f"api/asset/add/{char_code}/{name}/{capital}/{interest}")
    assert 1 == len(client.application.portfolio.children)
    assert 200 == response.status_code


def test_add_asset_list(client):
    char_code = "USD"
    name = "asset"
    capital = "100.0"
    interest = "0.5"
    expected_list = [[char_code, name, float(capital), float(interest)]]
    _ = client.get(f"api/asset/add/{char_code}/{name}/{capital}/{interest}")
    response = client.get(f"api/asset/list")

    assert expected_list == response.get_json()


def test_get_asset_by_name(client):
    char_code = "USD"
    name = "asset"
    capital = "100.0"
    interest = "0.5"
    expected_list = [[char_code, name, float(capital), float(interest)]]
    _ = client.get(f"api/asset/add/{char_code}/{name}/{capital}/{interest}")

    response = client.get(f"api/asset/get?name=asset")
    assert expected_list == response.get_json()


def test_calculate_revenue(client):
    client.application.portfolio.children = []
    years = 1
    char_code = "USD"
    name = "asset1"
    capital = "100.0"
    interest = "0.5"
    asset = Asset(char_code, name, float(capital), float(interest))
    _ = client.get(f"api/asset/add/{char_code}/{name}/{capital}/{interest}")

    response_indicators = client.get("/cbr/key_indicators")
    rates = response_indicators.get_json()
    response_rates = client.get("/cbr/daily")
    rates.update(response_rates.get_json())

    expected_value = {str(years): asset.calculate_revenue(years, rates[char_code])}
    response = client.get(f"/api/asset/calculate_revenue?period={years}")
    calculated_value = response.get_json()
    assert expected_value == calculated_value


def test_cleanup(client):
    response = client.get("api/asset/cleanup")
    assert 200 == response.status_code
    assert 0 == len(client.application.portfolio.children)
