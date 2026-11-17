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
import sys
from enum import Enum

if sys.version_info >= (3, 11):
    # pylint: disable=unused-import
    from enum import StrEnum  # nopycln: import
else:

    class StrEnum(str, Enum):
        # Match enum.StrEnum on Python 3.11+: str() is the member's value, not
        # "ClassName.MEMBER". Drivers that convert str subclasses with str()
        # (e.g. mysqlclient 2.3.1) would otherwise store the member's name.
        __str__ = str.__str__
