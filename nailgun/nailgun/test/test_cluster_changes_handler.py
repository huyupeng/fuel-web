# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp

from mock import Mock, patch
from netaddr import IPNetwork

import nailgun
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, IPAddr, Task
from nailgun.api.models import Network, NetworkGroup


class TestHandlers(BaseHandlers):

    @patch('nailgun.rpc.cast')
    def test_deploy_cast_with_right_args(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={
                "mode": "ha",
                "type": "compute"
            },
            nodes_kwargs=[
                {"role": "controller", "pending_addition": True},
                {"role": "controller", "pending_addition": True},
            ]
        )
        cluster_db = self.env.clusters[0]

        cluster_depl_mode = 'ha_compute'

        nailgun.task.task.Cobbler = Mock()
        supertask = self.env.launch_deployment()
        deploy_task_uuid = [x.uuid for x in supertask.subtasks
                            if x.name == 'deployment'][0]

        msg = {'method': 'deploy', 'respond_to': 'deploy_resp',
               'args': {}}
        cluster_attrs = cluster_db.attributes.merged_attrs_values()

        nets_db = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id).all()
        for net in nets_db:
            cluster_attrs[net.name + '_network_range'] = net.cidr

        management_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id).filter_by(
                name='management').first()
        management_vip = str(IPNetwork(management_net.cidr)[4])
        public_net = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster_db.id).filter_by(
                name='public').first()
        public_vip = str(IPNetwork(public_net.cidr)[4])
        cluster_attrs['management_vip'] = management_vip
        cluster_attrs['public_vip'] = public_vip
        cluster_attrs['deployment_mode'] = cluster_depl_mode
        cluster_attrs['network_manager'] = "FlatDHCPManager"

        msg['args']['attributes'] = cluster_attrs
        msg['args']['task_uuid'] = deploy_task_uuid
        nodes = []
        for n in self.env.nodes:
            node_ips = self.db.query(IPAddr).filter_by(node=n.id).all()
            node_ip = [ne.ip_addr + "/24" for ne in node_ips]
            nodes.append({'uid': n.id, 'status': n.status, 'ip': n.ip,
                          'error_type': n.error_type, 'mac': n.mac,
                          'role': n.role, 'id': n.id, 'fqdn': n.fqdn,
                          'progress': 0, 'meta': n.meta, 'online': True,
                          'network_data': [{'brd': '172.16.0.255',
                                            'ip': node_ip[0],
                                            'vlan': 103,
                                            'gateway': '172.16.0.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': 'management'},
                                           {'brd': '240.0.1.255',
                                            'ip': node_ip[1],
                                            'vlan': 104,
                                            'gateway': '240.0.1.1',
                                            'netmask': '255.255.255.0',
                                            'dev': 'eth0',
                                            'name': 'public'},
                                           {'vlan': 100,
                                            'name': 'floating',
                                            'dev': 'eth0'},
                                           {'vlan': 101,
                                            'name': 'fixed',
                                            'dev': 'eth0'},
                                           {'vlan': 102,
                                            'name': 'storage',
                                            'dev': 'eth0'}]})
        msg['args']['nodes'] = nodes

        nailgun.task.task.rpc.cast.assert_called_once_with(
            'naily', msg)

    @patch('nailgun.rpc.cast')
    def test_deploy_and_remove_correct_nodes_and_statuses(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"status": "ready"},
                {"pending_addition": True},
                {"pending_deletion": True, "status": "error"},
            ]
        )

        nailgun.task.task.Cobbler = Mock()
        self.env.launch_deployment()

        # remove_nodes method call
        n_rpc = nailgun.task.task.rpc.cast. \
            call_args_list[0][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc), 1)
        n_removed_rpc = [
            n for n in n_rpc if n['uid'] == self.env.nodes[2].id
        ][0]
        # object is found, so we passed the right node for removal
        self.assertIsNotNone(n_removed_rpc)

        # deploy method call
        n_rpc = nailgun.task.task.rpc.cast. \
            call_args_list[1][0][1]['args']['nodes']
        self.assertEquals(len(n_rpc), 2)
        n_provisioned_rpc = [
            n for n in n_rpc if n['uid'] == self.env.nodes[0].id
        ][0]
        n_added_rpc = [
            n for n in n_rpc if n['uid'] == self.env.nodes[1].id
        ][0]

        self.assertEquals(n_provisioned_rpc['status'], 'provisioned')
        self.assertEquals(n_added_rpc['status'], 'provisioning')

    @patch('nailgun.rpc.cast')
    def test_deploy_reruns_after_network_changes(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"status": "ready"},
                {
                    "pending_deletion": True,
                    "status": "ready",
                    "role": "compute"
                },
            ]
        )

        # for clean experiment
        cluster_db = self.env.clusters[0]
        cluster_db.clear_pending_changes()
        cluster_db.add_pending_changes('networks')

        for n in self.env.nodes:
            self.assertEqual(n.needs_redeploy, True)

        nailgun.task.task.Cobbler = Mock()
        self.env.launch_deployment()
