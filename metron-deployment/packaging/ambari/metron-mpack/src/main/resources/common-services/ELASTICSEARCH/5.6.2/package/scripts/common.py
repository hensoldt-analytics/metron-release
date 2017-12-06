#!/usr/bin/env python
"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from ambari_commons.os_check import OSCheck
from resource_management.core.logger import Logger

def get_env_path(default="/etc/default/elasticsearch"):
    """
    Defines the path to the Elasticsearch environment file.  This path will
    differ based on the OS family.
    :param default: The path used if the OS family is not recognized.
    """
    path = default
    if OSCheck.is_redhat_family():
      path = "/etc/sysconfig/elasticsearch"
    elif OSCheck.is_ubuntu_family():
      path = "/etc/default/elasticsearch"
    else:
      Logger.error("Unexpected OS family; using default path={0}".format(path))

    return path
