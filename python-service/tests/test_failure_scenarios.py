import pytest


class TimeoutProvider:
    def generate(self, *args, **kwargs):
        raise TimeoutError("provider timeout")


class UnavailableProvider:
    def generate(self, *args, **kwargs):
        raise ConnectionError("provider unavailable")


class MalformedProvider:
    def generate(self, *args, **kwargs):
        return "invalid structured response"


def test_provider_timeout_is_technical_failure():
    provider = TimeoutProvider()

    with pytest.raises(TimeoutError):
        provider.generate("test")


def test_provider_unavailable_is_technical_failure():
    provider = UnavailableProvider()

    with pytest.raises(ConnectionError):
        provider.generate("test")


def test_malformed_provider_output_is_detectable():
    provider = MalformedProvider()

    result = provider.generate("test")

    assert isinstance(result, str)
    assert result == "invalid structured response"