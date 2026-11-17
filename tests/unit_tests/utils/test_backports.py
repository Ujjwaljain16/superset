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
from superset.common.db_query_status import QueryStatus
from superset.utils.backports import StrEnum


class Color(StrEnum):
    RED = "red"


def test_str_enum_str_is_the_value() -> None:
    """
    ``str()`` of a member must be its value, as with ``enum.StrEnum`` on
    Python 3.11+. The Python 3.10 backport used to return ``"Color.RED"``.
    """
    assert str(Color.RED) == "red"
    assert f"{Color.RED}" == "red"
    assert Color.RED == "red"


def test_query_status_str_is_the_value() -> None:
    """
    Some database drivers convert ``str`` subclasses with ``str()``
    (mysqlclient 2.3.1 does), so ``query.status`` was written as
    ``"QueryStatus.SUCCESS"`` on Python 3.10 (apache/superset#46238).
    """
    assert str(QueryStatus.SUCCESS) == "success"
