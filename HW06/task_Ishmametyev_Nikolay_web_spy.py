from argparse import ArgumentParser
import requests
from bs4 import BeautifulSoup

DEFAULT_GITLAB_URL = "https://about.gitlab.com/features/"


def find_free_products(bs_obj: BeautifulSoup):
    """Find all free products from BeautifulSoup class"""
    free_products = bs_obj.find_all("a", attrs={"title": "Available in GitLab SaaS Free"})
    return free_products


def find_paid_products(bs_obj: BeautifulSoup):
    """Find all paid products from BeautifulSoup class"""
    paid_products = bs_obj.find_all("a", attrs={"title": "Not available in SaaS Free"})
    return paid_products


def build_bs_object_from_response(url):
    """Build BeautifulSoup from request.get"""
    response = requests.get(url)
    bs_obj = BeautifulSoup(response.text, "html.parser")
    return bs_obj


def print_number_of_competitor_products(site):
    if site == "gitlab":
        bs_obj = build_bs_object_from_response(DEFAULT_GITLAB_URL)
        free_products = find_free_products(bs_obj)
        paid_products = find_paid_products(bs_obj)
        print(f"free products: {len(free_products)}")
        print(f"enterprise products: {len(paid_products)}")
    else:
        pass


def process_cli_arguments(arguments):
    print_number_of_competitor_products(arguments.site)


def setup_parser(parser):
    """Setup parser for CLI launch"""
    parser.add_argument("site")
    parser.set_defaults(callback=process_cli_arguments)


def main():
    parser = ArgumentParser(
        prog="Web-spy",
        description="Check number of paid products on web-site",
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
