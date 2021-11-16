from argparse import ArgumentParser
import pytest
import asset as lib

ASSET_EXAMPLE_STR = 'property   1000    0.1'


@pytest.fixture()
def example_dataset_io(tmpdir):
    dataset_fio = tmpdir.join('asset.txt')
    dataset_fio.write(ASSET_EXAMPLE_STR)
    return dataset_fio



# def test_open_yaml_config(tmpdir):
#     dataset_fio = tmpdir.join('config.log.yml')
#     # dataset_fio.write(EXAMPLE_YAML_CONFIG)
#     with open(dataset_fio, 'w') as outfile:
#         yaml.dump(EXAMPLE_YAML_CONFIG, outfile, default_flow_style=False)
#     lib.setup_logging(dataset_fio)
#     assert 1


def test_load_asset(example_dataset_io):
    expected_asset = lib.Asset.build_from_str(ASSET_EXAMPLE_STR)
    loaded_asset = lib.load_asset_from_file(example_dataset_io)
    assert expected_asset == loaded_asset


def test_calculate_revenue():
    years = 3
    asset = lib.Asset.build_from_str(ASSET_EXAMPLE_STR)
    expected_revenue = asset.capital * ((1.0 + asset.interest) ** years - 1.0)
    calculated_revenue = asset.calculate_revenue(years)
    assert expected_revenue == calculated_revenue


def test_setup_default_logging():
    lib.setup_logging(None)
    assert 1 == 1


def test_print_asset_revenue_threshold(example_dataset_io, caplog, capsys):
    caplog.set_level('DEBUG')
    lib.setup_logging(None)
    num_periods = [1, 2, 3, 4, 5]
    message = 'too many periods were provided: %s' % len(num_periods)
    lib.print_asset_revenue(example_dataset_io, num_periods)
    assert any('' in m for m in caplog.messages), (
        "There is no warning: '%s' in logs" % message
    )

    captures = capsys.readouterr()
    # from pdb import set_trace; set_trace();
    assert "building asset object..." not in captures.err
    assert "too many periods were provided: %s" % len(num_periods) in captures.err


def test_print_asset_revenue(example_dataset_io, caplog):
    caplog.set_level('DEBUG')
    num_periods = [1, 2]
    message = 'asset %s for period %s gives %s'
    lib.print_asset_revenue(example_dataset_io, num_periods)
    assert any(message == vars(m)['msg'] for m in caplog.records), (
        "There is no debug message: '%s' in logs" % message
    )





def test_setup_parser():
    parser = ArgumentParser(
        prog="asset",
        description="tool to forecast asset revenue",
    )
    lib.setup_parser(parser)
    assert 1 == 1

