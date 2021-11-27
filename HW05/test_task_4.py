from unittest.mock import patch
import pytest
from asset_with_external_dependency import Asset


@patch("cbr.get_usd_course")
def test_can_mock_external_calls(mock_get_usd_course):
    mock_get_usd_course.side_effect = [76.54, 77.44, ConnectionError]

    asset_property = Asset(name="property", capital=10**6, interest=0.1)
    assert asset_property.calculate_revenue_from_usd(years=1) == pytest.approx(76.54 * 10**5, abs=0.01)
    assert asset_property.calculate_revenue_from_usd(years=1) == pytest.approx(77.44 * 10**5, abs=0.01)
    with pytest.raises(ConnectionError):
        asset_property.calculate_revenue_from_usd(years=1)
