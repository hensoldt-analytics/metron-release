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

import os

from ambari_commons.os_check import OSCheck
from common import get_env_path
from resource_management.core.resources.system import Execute
from resource_management.core.resources.system import Directory
from resource_management.core.resources.system import File
from resource_management.core.source import InlineTemplate
from resource_management.core.source import Template
from resource_management.core.resources import User
from resource_management.core.logger import Logger
from resource_management.libraries.functions import format as ambari_format
from resource_management.libraries.functions.get_user_call_output import get_user_call_output

def elastic():
    import params

    Logger.info("Creating user: {0}:{1}".format(params.elastic_user, params.elastic_group))
    User(params.elastic_user, action = "create", groups = params.elastic_group)

    params.path_data = params.path_data.replace('"', '')
    data_path = params.path_data.replace(' ', '').split(',')
    data_path[:] = [x.replace('"', '') for x in data_path]
    directories = [params.log_dir, params.pid_dir, params.conf_dir]
    directories = directories + data_path + ["{0}/scripts".format(params.conf_dir)]

    Logger.info("Creating directories: {0}".format(directories))
    Directory(directories,
              create_parents=True,
              mode=0755,
              owner=params.elastic_user,
              group=params.elastic_group
              )

    Logger.info("Elasticsearch env: ""{0}/elastic-env.sh".format(params.conf_dir))
    File("{0}/elastic-env.sh".format(params.conf_dir),
         owner=params.elastic_user,
         group=params.elastic_group,
         content=InlineTemplate(params.elastic_env_sh_template)
         )

    configurations = params.config['configurations']['elastic-site']
    Logger.info("Elasticsearch yml: ""{0}/elasticsearch.yml".format(params.conf_dir))
    File("{0}/elasticsearch.yml".format(params.conf_dir),
         content=Template(
             "elasticsearch.master.yaml.j2",
             configurations=configurations),
         owner=params.elastic_user,
         group=params.elastic_group
         )

    elastic_env_path = get_env_path()
    Logger.info("Elasticsearch sysconfig: path={0}".format(elastic_env_path))
    File(elastic_env_path,
         owner="root",
         group="root",
         content=InlineTemplate(params.sysconfig_template)
         )

    # in some OS this folder may not exist, so create it
    Logger.info("Elasticsearch; Ensure PAM limits directory exists: {0}".format(params.limits_conf_dir))
    Directory(params.limits_conf_dir,
              create_parents=True,
              owner='root',
              group='root'
              )

    Logger.info("Elasticsearch PAM limits: {0}".format(params.limits_conf_file))
    File(params.limits_conf_file,
         content=Template('elasticsearch_limits.conf.j2'),
         owner="root",
         group="root"
         )

    # is the platform running systemd?
    Logger.info("Is platform running systemd?")
    rc, out, err = get_user_call_output("pidof systemd", "root", is_checked_call=False)
    if rc == 0:
        Logger.info("Systemd found; configuring for Elasticsearch");

        # ensure the systemd directory for elasticsearch overrides exists
        Logger.info("Create systemd directory for Elasticsearch: {0}".format(params.systemd_elasticsearch_dir))
        Directory(params.systemd_elasticsearch_dir,
                  create_parents=True,
                  owner='root',
                  group='root')

        # when using Elasticsearch packages on systems that use systemd, system
        # limits must also be specified via systemd.
        # see https://www.elastic.co/guide/en/elasticsearch/reference/5.6/setting-system-settings.html#systemd
        Logger.info("Elasticsearch systemd limits: {0}".format(params.systemd_override_file))
        File(params.systemd_override_file,
             content=InlineTemplate(params.systemd_override_template),
             owner="root",
             group="root")

        # reload the configuration
        Execute("systemctl daemon-reload")