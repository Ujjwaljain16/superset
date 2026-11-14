# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from typing import Any
from unittest.mock import MagicMock

from pytest_mock import MockerFixture


def test_delete_tag_by_pk_routes_through_delete_tags_command(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """
    Regression test: ``DELETE /api/v1/tag/<pk>`` used to fall through to the
    FAB-generated single-object delete route, which deletes the row directly
    via the datamodel and never runs ``DeleteTagsCommand.validate`` (the
    admin-or-creator check, and the system-tag refusal). The pk route must
    be overridden to share that same validation instead of duplicating it.
    """
    mock_tag = MagicMock(id=1)
    mock_tag.name = "example_tag"
    mocker.patch("superset.tags.api.TagDAO.find_by_id", return_value=mock_tag)
    mock_command = mocker.patch("superset.tags.api.DeleteTagsCommand")
    mock_command.return_value.run.return_value = None

    response = client.delete("/api/v1/tag/1")

    assert response.status_code == 200
    mock_command.assert_called_once_with(["example_tag"])


def test_delete_tag_by_pk_not_found(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """DELETE /api/v1/tag/<pk> returns 404 when the tag does not exist."""
    mocker.patch("superset.tags.api.TagDAO.find_by_id", return_value=None)
    mock_command = mocker.patch("superset.tags.api.DeleteTagsCommand")

    response = client.delete("/api/v1/tag/999")

    assert response.status_code == 404
    mock_command.assert_not_called()


def test_delete_tag_by_pk_denied_surfaces_as_422(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """
    A non-admin, non-creator caller (or an attempt to delete a system tag)
    is rejected by DeleteTagsCommand.validate with TagInvalidError; the pk
    route must surface that as 422, not silently succeed.
    """
    from superset.commands.tag.exceptions import TagInvalidError

    mock_tag = MagicMock(id=1)
    mock_tag.name = "someone_elses_tag"
    mocker.patch("superset.tags.api.TagDAO.find_by_id", return_value=mock_tag)
    mock_command = mocker.patch("superset.tags.api.DeleteTagsCommand")
    mock_command.return_value.run.side_effect = TagInvalidError()

    response = client.delete("/api/v1/tag/1")

    assert response.status_code == 422


def test_delete_tag_by_pk_denied_with_populated_exceptions_surfaces_as_422(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """
    Regression test for an AttributeError that only surfaced once
    DeleteTagsCommand.validate's TagInvalidError actually carried the
    exceptions it composites at runtime (a plain TagDeleteFailedError,
    not a ValidationError). The pk route calls
    ``ex.normalized_messages()`` on the TagInvalidError it catches, which
    previously crashed with a 500 instead of returning 422 because
    TagDeleteFailedError has no ``normalized_messages()`` method. A
    TagInvalidError() with no exceptions (as in the test above) does not
    exercise that aggregation loop, so this test populates it the way the
    real command does.
    """
    from superset.commands.tag.exceptions import (
        TagDeleteForbiddenValidationError,
        TagInvalidError,
    )

    mock_tag = MagicMock(id=1)
    mock_tag.name = "system:some_type"
    mocker.patch("superset.tags.api.TagDAO.find_by_id", return_value=mock_tag)
    mock_command = mocker.patch("superset.tags.api.DeleteTagsCommand")
    mock_command.return_value.run.side_effect = TagInvalidError(
        exceptions=[
            TagDeleteForbiddenValidationError(
                "Tag system:some_type is a system tag and cannot be deleted"
            )
        ]
    )

    response = client.delete("/api/v1/tag/1")

    assert response.status_code == 422
    assert "tags" in response.json["message"]


def test_delete_tag_by_pk_race_with_bulk_delete_surfaces_as_404(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """
    If the tag is deleted concurrently between the ``find_by_id`` lookup and
    ``DeleteTagsCommand.validate``'s own lookup, the command raises
    TagNotFoundError; the pk route must surface that as 404.
    """
    from superset.commands.tag.exceptions import TagNotFoundError

    mock_tag = MagicMock(id=1)
    mock_tag.name = "example_tag"
    mocker.patch("superset.tags.api.TagDAO.find_by_id", return_value=mock_tag)
    mock_command = mocker.patch("superset.tags.api.DeleteTagsCommand")
    mock_command.return_value.run.side_effect = TagNotFoundError("example_tag")

    response = client.delete("/api/v1/tag/1")

    assert response.status_code == 404


def test_delete_tag_by_pk_delete_failed_surfaces_as_422(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """DeleteTagsCommand raising TagDeleteFailedError surfaces as 422."""
    from superset.commands.tag.exceptions import TagDeleteFailedError

    mock_tag = MagicMock(id=1)
    mock_tag.name = "example_tag"
    mocker.patch("superset.tags.api.TagDAO.find_by_id", return_value=mock_tag)
    mock_command = mocker.patch("superset.tags.api.DeleteTagsCommand")
    mock_command.return_value.run.side_effect = TagDeleteFailedError()

    response = client.delete("/api/v1/tag/1")

    assert response.status_code == 422


def test_create_tag_rejects_name_longer_than_the_column(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """
    ``tag.name`` is ``VARCHAR(250)``. A longer name used to pass validation,
    fail at the database and surface as a 500 ("Tag could not be created.");
    it must be a 400 that names the field.
    """
    mock_command = mocker.patch(
        "superset.tags.api.CreateCustomTagWithRelationshipsCommand"
    )

    response = client.post("/api/v1/tag/", json={"name": "x" * 251})

    assert response.status_code == 400
    assert "name" in response.json["message"]
    mock_command.assert_not_called()


def test_create_tag_accepts_name_at_the_column_limit(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """A name of exactly 250 characters fits the column and must still be accepted."""
    mock_command = mocker.patch(
        "superset.tags.api.CreateCustomTagWithRelationshipsCommand"
    )

    response = client.post("/api/v1/tag/", json={"name": "x" * 250})

    assert response.status_code == 201
    mock_command.assert_called_once()


def test_bulk_create_tags_rejects_name_longer_than_the_column(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """``bulk_create`` validates each tag with the same schema as ``POST /tag/``."""
    mock_command = mocker.patch(
        "superset.tags.api.CreateCustomTagWithRelationshipsCommand"
    )

    response = client.post(
        "/api/v1/tag/bulk_create",
        json={"tags": [{"name": "ok"}, {"name": "x" * 251}]},
    )

    assert response.status_code == 400
    mock_command.assert_not_called()


def test_update_tag_rejects_name_longer_than_the_column(
    client: Any,
    full_api_access: None,
    mocker: MockerFixture,
) -> None:
    """Renaming a tag to a name longer than the column is a 400, not a 500."""
    mock_command = mocker.patch("superset.tags.api.UpdateTagCommand")

    response = client.put("/api/v1/tag/1", json={"name": "x" * 251})

    assert response.status_code == 400
    mock_command.assert_not_called()
