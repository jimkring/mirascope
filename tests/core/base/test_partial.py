"""Tests that `partial` works to make all fields optional."""

from pydantic import BaseModel

from mirascope.core.base._partial import partial


class ShallowModel(BaseModel):
    """A test model."""

    param: str
    default: int = 0


class PartialShallowModel(BaseModel):
    """A test model."""

    param: str | None = None
    default: int | None = None


def test_shallow_partial():
    """Tests that `Partial` works to make all fields optional in a shallow model."""
    assert (
        partial(ShallowModel).model_json_schema()
        == PartialShallowModel.model_json_schema()
    )


class DeeperModel(BaseModel):
    """A deeper model."""

    shallow: ShallowModel
    param: str


class PartialDeeperModel(BaseModel):
    """A deeper model."""

    shallow: PartialShallowModel | None = {}  # pyright: ignore [reportAssignmentType]
    param: str | None = None


def test_deeper_partial():
    """Tests that `Partial` works to make all fields optional in a deeper model."""
    assert (
        partial(DeeperModel).model_json_schema()
        == PartialDeeperModel.model_json_schema()
    )


class DeepestModel(BaseModel):
    """A deepest model."""

    shallow: ShallowModel
    deeper: DeeperModel
    param: str


class PartialDeepestModel(BaseModel):
    """A deepest model."""

    shallow: PartialShallowModel | None = {}  # pyright: ignore [reportAssignmentType]
    deeper: PartialDeeperModel | None = {}  # pyright: ignore [reportAssignmentType]
    param: str | None = None


def test_deepest_partial():
    """Tests that `Partial` works to make all fields optional in a deeper model."""
    assert (
        partial(DeepestModel).model_json_schema()
        == PartialDeepestModel.model_json_schema()
    )
