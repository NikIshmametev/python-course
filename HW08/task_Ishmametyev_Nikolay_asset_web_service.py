from typing import Dict, List
from collections import defaultdict

from bs4 import BeautifulSoup
from flask import Flask, jsonify, redirect, request
import requests


app = Flask(__name__)

URL_CBR_DAILY = "https://www.cbr.ru/eng/currency_base/daily/"
URL_CBR_KEY_INDICATORS = "https://www.cbr.ru/eng/key-indicators/"

DAILY_CURRENCY_TABLE_PARAMS = {
    "column_idx": {
        "char сode": 1,  # Вторая с на русском!
        "unit": 2,
        "rate": 4,
    }
}

KEY_INDICATORS_TABLE_PARAMS = {
    "table_idx": [1, 2],  # 1: currency, 2: metals
    "indicators_per_table": {
        1: ["USD", "EUR"],
        2: ["Au", "Ag", "Pd", "Pt"]
    },
    "reserve_currency": ["USD", "EUR"]
}


class Asset:
    def __init__(self, char_code: str, name: str, capital: float, interest: float):
        self.name = name
        self.capital = capital
        self.char_code = char_code
        self.interest = interest

    @classmethod
    def build_from_str(cls, raw: str):
        char_code, name, capital, interest = raw.strip().split()
        capital = float(capital)
        interest = float(interest)
        asset = cls(char_code=char_code, name=name, capital=capital, interest=interest)
        return asset

    def calculate_revenue(self, years: int, currency_rate: float) -> float:
        revenue = self.capital * ((1.0 + self.interest) ** years - 1.0)
        revenue *= currency_rate
        return revenue

    def __repr__(self):
        repr_ = f"{self.__class__.__name__}({self.name}, {self.capital}, {self.interest})"
        return repr_

    def __eq__(self, rhs):
        outcome = (
            self.name == rhs.name
            and self.capital == rhs.capital
            and self.interest == rhs.interest
            and self.char_code == rhs.char_code
        )
        return outcome


class Portfolio:
    def __init__(self) -> None:
        self.children: List[Asset] = []

    def __len__(self):
        return len(self.children)

    def _check_asset_exist(self, asset: Asset):
        for child in self.children:
            if asset.name == child.name:
                return True
        return False

    def add(self, asset: Asset):
        if self._check_asset_exist(asset):
            raise ValueError
        self.children.append(asset)
        asset.parent = self

    def find_asset(self, asset_name):
        for child in self.children:
            if asset_name == child.name:
                return child
        return None

    def calculate_revenue(self, years: int, currency_rate_dict: Dict):
        results = []
        for child in self.children:
            currency_rate = currency_rate_dict.get(child.char_code) or 1  # Ruble or another asset
            results.append(child.calculate_revenue(years=years, currency_rate=currency_rate))
        return sum(results)


def parse_row_from_daily_currency_table(bs_obj):
    char_code_idx = DAILY_CURRENCY_TABLE_PARAMS["column_idx"]["char сode"]
    unit_idx = DAILY_CURRENCY_TABLE_PARAMS["column_idx"]["unit"]
    rate_idx = DAILY_CURRENCY_TABLE_PARAMS["column_idx"]["rate"]

    char_code = bs_obj.find_all("td")[char_code_idx].text
    unit = float(bs_obj.find_all("td")[unit_idx].text)
    rate = float(bs_obj.find_all("td")[rate_idx].text)
    return char_code, rate/unit


def parse_row_from_key_indicators_table(bs_obj_for_row, indicators: List):
    row_text = bs_obj_for_row.get_text().strip().split("\n")
    row_text_without_symbols = [s_ for s_ in row_text if s_]
    for indicator in indicators:
        if indicator in row_text:
            rate = float(row_text_without_symbols[-1].replace(",", ""))
            return indicator, rate
    return None, None


def extract_cbr_daily_data_obj(html_data: str):
    bs_obj = BeautifulSoup(html_data, "html.parser")
    table_data = bs_obj.find_all("tr")
    return table_data


def extract_cbr_key_indicators_data_obj(html_data: str):
    bs_obj = BeautifulSoup(html_data, "html.parser")
    multiple_table_data = bs_obj.find_all("table")
    return multiple_table_data


def remove_reserved_currency(rates: Dict):
    for currency in KEY_INDICATORS_TABLE_PARAMS["reserve_currency"]:
        if currency in rates:
            del rates[currency]
    return rates


def parse_cbr_currency_base_daily(html_data: str) -> Dict[str, float]:
    rates = dict()
    table_data = extract_cbr_daily_data_obj(html_data)

    for row in table_data[1:]:  # Miss header
        char_code, rate = parse_row_from_daily_currency_table(row)
        rates[char_code] = rate
    rates = remove_reserved_currency(rates)
    return rates


def parse_cbr_key_indicators(html_data: str) -> Dict[str, float]:
    indicators = dict()
    multiple_table_data = extract_cbr_key_indicators_data_obj(html_data)
    for table_data in multiple_table_data:
        if "US Dollar" in table_data.text:
            for row in table_data.find_all("tr"):
                char_code, rate = parse_row_from_key_indicators_table(
                    row, KEY_INDICATORS_TABLE_PARAMS["indicators_per_table"][1])
                if char_code:
                    indicators[char_code] = rate
        elif "Au" in table_data.text:
            for row in table_data.find_all("tr"):
                char_code, rate = parse_row_from_key_indicators_table(
                    row, KEY_INDICATORS_TABLE_PARAMS["indicators_per_table"][2])
                if char_code:
                    indicators[char_code] = rate
    return indicators


def choose_endpoint_by_char_code(char_code: str):
    key_indicators_char_code = []
    for char_codes in KEY_INDICATORS_TABLE_PARAMS["indicators_per_table"].values():
        key_indicators_char_code.append(char_codes)
    if char_code in key_indicators_char_code:
        return "get_cbr_key_indicators"
    return "get_cbr_daily_currency_rates"


"""Endpoints"""
app.portfolio = Portfolio()


@app.route("/cbr/daily")
def get_cbr_daily_currency_rates() -> Dict[str, float]:
    try:
        response = requests.get(URL_CBR_DAILY)
        rates = parse_cbr_currency_base_daily(response.text)
        return jsonify(rates)
    except requests.exceptions.ConnectionError:
        redirect("connection_error", 503)


@app.route("/cbr/key_indicators")
def get_cbr_key_indicators() -> Dict[str, float]:
    try:
        response = requests.get(URL_CBR_KEY_INDICATORS)
        indicators = parse_cbr_key_indicators(response.text)
        return jsonify(indicators)
    except requests.exceptions.ConnectionError:
        redirect("connection_error", 503)


@app.route("/api/asset/add/<char_code>/<name>/<capital>/<interest>")
def add_asset(char_code, name, capital, interest):
    asset = Asset(char_code, name, float(capital), float(interest))
    try:
        app.portfolio.add(asset)
        return f"Asset '{name}' was successfully added", 200
    except ValueError:
        return "", 403


@app.route("/api/asset/list")
def list_all_asset():
    assets = [[asset.char_code, asset.name, asset.capital, asset.interest]
              for asset in app.portfolio.children]
    sorted_assets = sorted(assets, key=lambda x: (x[0], x[1], x[2], x[3]))
    return jsonify(sorted_assets)


@app.route("/api/asset/get")
def get_asset_by_name():
    asset_names = request.args.getlist("name")
    if not asset_names:
        return jsonify("")
    assets_found_by_name = [app.portfolio.find_asset(asset_name)
                            for asset_name in asset_names if app.portfolio.find_asset(asset_name)]
    assets = [[asset.char_code, asset.name, asset.capital, asset.interest]
              for asset in assets_found_by_name]
    sorted_assets = sorted(assets, key=lambda x: (x[0], x[1], x[2], x[3]))
    return jsonify(sorted_assets)


@app.route("/api/asset/calculate_revenue")
def calculate_revenue():
    period_collection = request.args.getlist("period")
    if not period_collection:
        return jsonify("")
    period_revenue = defaultdict(lambda: 0)
    rates = get_cbr_daily_currency_rates().get_json()
    indicators = get_cbr_key_indicators().get_json()
    rates.update(indicators)

    for period in period_collection:
        period_revenue[period] = app.portfolio.calculate_revenue(int(period), rates)
    return jsonify(period_revenue)


@app.route("/api/asset/cleanup")
def cleanup_assets():
    app.portfolio = Portfolio()
    return "there are no more assets", 200


@app.errorhandler(404)
def page_not_found(e):
    return "This route is not found", 404


@app.errorhandler(503)
def connection_error(e):
    return "CBR service is unavailable", 503
