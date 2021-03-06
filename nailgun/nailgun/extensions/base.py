# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"Contains base class for Nailgun extensions"

import abc

import six


class BasePipeline(object):

    @classmethod
    def process_deployment(cls, deployment_data, cluster, nodes, **kwargs):
        """Change the deployment_data.

        :param deployment_data: serialized data
        """
        return deployment_data

    @classmethod
    def process_provisioning(cls, provisioning_data, cluster, nodes, **kwargs):
        """Change the provisioning_data.

        :param provisioning_data: serialized data
        """
        return provisioning_data


@six.add_metaclass(abc.ABCMeta)
class BaseExtension(object):
    """Base class for Nailgun extension

    If extension provides API, define here urls in then following format:
    urls = [
      {
        "uri": r'/new/url',
        "handler": HandlerClass
      }
    ]

    If extension needs to manipulate provisioning or deployment data it should
    define data_pipelines list which is a list of BasePipeline sub-classes:

    data_pipelines = [
        ExamplePipelineClass,
        ExamplePipelineClass2,
    ]

    Specify a list of calls which extension provides (not required):

    provides = [
        'method_1',
        'method_2',
    ]

    """
    urls = []
    data_pipelines = []
    provides = []

    @classmethod
    def alembic_migrations_path(cls):
        """Path to alembic migrations (if extension provides any)"""
        return None

    @abc.abstractproperty
    def name(self):
        """Uniq name of the extension."""

    @abc.abstractproperty
    def description(self):
        """Brief description of extension"""

    @abc.abstractproperty
    def version(self):
        """Version of the extension

        Follows semantic versioning schema (http://semver.org/)
        """

    @classmethod
    def full_name(cls):
        """Returns extension's name and version in human readable format"""
        return '{0}-{1}'.format(cls.name, cls.version)

    @classmethod
    def table_prefix(cls):
        return '{0}_'.format(cls.name)

    @classmethod
    def alembic_table_version(cls):
        return '{0}alembic_version'.format(cls.table_prefix())

    @classmethod
    def setup_yaql_context(cls, yaql_context):
        """Setup YAQL context that is going to be used for serialization"""

    @classmethod
    def on_node_create(cls, node):
        """Callback which gets executed when node is created"""

    @classmethod
    def on_node_update(cls, node):
        """Callback which gets executed when node is updated"""

    @classmethod
    def on_node_reset(cls, node):
        """Callback which gets executed when node is reseted"""

    @classmethod
    def on_node_delete(cls, node):
        """Callback which gets executed when node is deleted"""

    @classmethod
    def on_remove_node_from_cluster(cls, node):
        """Callback which gets executed when node is removed from a cluster"""

    @classmethod
    def on_node_collection_delete(cls, node_ids):
        """Callback which gets executed when node collection is deleted"""

    @classmethod
    def on_nodegroup_create(cls, nodegroup):
        """Callback which gets executed when node group is created"""

    @classmethod
    def on_nodegroup_delete(cls, nodegroup):
        """Callback which gets executed when node group is deleted"""

    @classmethod
    def on_cluster_create(cls, cluster, data):
        """Callback which gets executed when cluster is initially created.

        This is called after the cluster object is created, attributes have
        been created and the default extensions list has been set.
        """

    @classmethod
    def on_cluster_patch_attributes(cls, cluster, public_map):
        """Callback which gets executed when cluster attributes are updated"""

    @classmethod
    def on_cluster_delete(cls, cluster):
        """Callback which gets executed when cluster is deleted"""

    @classmethod
    def on_before_deployment_check(cls, cluster):
        """Callback which gets executed when "before deployment check" runs"""

    @classmethod
    def on_before_deployment_serialization(cls, cluster, nodes,
                                           ignore_customized):
        """Callback which gets executed before deployment serialization"""

    @classmethod
    def on_before_provisioning_serialization(cls, cluster, nodes,
                                             ignore_customized):
        """Callback which gets executed before provisioning serialization"""
