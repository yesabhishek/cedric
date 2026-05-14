import pytest

from cedric.models import ProjectSpec


def test_project_spec_normalizes_package_names():
    spec = ProjectSpec(name="My-API", framework="fastapi", database="sqlite")

    assert spec.normalized_package() == "my_api"
    assert spec.metadata()["framework"] == "fastapi"


def test_project_spec_rejects_invalid_names():
    with pytest.raises(ValueError):
        ProjectSpec(name="123-api", framework="fastapi")
