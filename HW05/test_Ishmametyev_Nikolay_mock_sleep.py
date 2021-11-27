import sleepy
from unittest.mock import patch


@patch('sleepy.sleep')
def test_sleep_add(mock_sleep):
    value = sleepy.sleep_add(1, 2)
    mock_sleep.assert_called_once()
    assert 3 == value


@patch('time.sleep')
def test_sleep_mult(mock_sleep):
    value = sleepy.sleep_multiply(1, 2)
    mock_sleep.assert_called_once()
    assert 2 == value

