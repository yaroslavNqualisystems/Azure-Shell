import traceback

from cloudshell.cp.azure.models.network_actions_models import SetAppSecurityGroupActionResult


class SetAppSecurityGroupsOperation(object):
    def __init__(self, vm_service, resource_id_parser, nsg_service, generic_lock_provider):
        """
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param AzureResourceIdParser resource_id_parser:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService nsg_service:
        :param cloudshell.cp.azure.domain.services.lock_service.GenericLockProvider generic_lock_provider:
        """
        self.vm_service = vm_service
        self.resource_id_parser = resource_id_parser
        self.nsg_service = nsg_service
        self.generic_lock_provider = generic_lock_provider

    def set_apps_security_groups(self, logger, app_security_group_models, compute_client, network_client, group_name):
        """
        Set custom security groups to a deployed app
        :param logging.Logger logger:
        :param list[AppSecurityGroupModel] app_security_group_models:
        :param str group_name:
        :return:
        """
        # purpose of set_apps_security_groups is to set custom security rules for specific apps.
        # the idea is that we can allow / block traffic to specific VMs

        # In general, we have two kinds of network security groups in Azure:
        # 1. NSG per VM
        # 2. an NSG for the sandbox, which handles security rules for the sandbox subnets.

        result = []
        for app_security_group_model in app_security_group_models:
            try:

                # get network security group for VM
                vm_name = app_security_group_model.deployed_app.name
                nsg_name = 'NSG_' + vm_name
                instance = self.vm_service.get_vm(compute_client, group_name, vm_name)
                nic_to_subnet_name_map = self._create_nic_to_subnet_name_map(network_client, instance, group_name)

                logger.info(
                    "Setting custom app security rules for {}.".format(app_security_group_model.deployed_app.name))

                for security_group_config in app_security_group_model.security_group_configurations:
                    subnet_name = self.resource_id_parser.get_name_from_resource_id(security_group_config.subnet_id)
                    nic = self._find_nic_by_subnet(nic_to_subnet_name_map, subnet_name)
                    destination_ip = nic.ip_configurations[0].private_ip_address
                    lock = self.generic_lock_provider.get_resource_lock(lock_key=nsg_name, logger=logger)

                    self.nsg_service.create_network_security_group_rules(network_client=network_client,
                                                                         group_name=group_name,
                                                                         security_group_name=nsg_name,
                                                                         inbound_rules=security_group_config.rules,
                                                                         destination_addr=destination_ip,
                                                                         lock=lock)

                action_result = self._create_security_group_action_result(
                    app_name=app_security_group_model.deployed_app.name,
                    is_success=True,
                    message='')

            except Exception as ex:
                message = "Setting custom app security rules failed for '{0}' with error '{1}'.".format(
                    app_security_group_model.deployed_app.name, ex.message)

                action_result = self._create_security_group_action_result(
                    app_name=app_security_group_model.deployed_app.name,
                    is_success=False,
                    message=message)

                logger.error("Setting custom app security rules failed for '{0}' with error '{1}'.".format(
                    app_security_group_model.deployed_app.name,
                    traceback.format_exc()))

            result.append(action_result)

        return result

    def _find_nic_by_subnet(self, nic_to_subnet_map, subnet_name):
        """
        :param dict nic_to_subnet_map:
        :param str subnet_name:
        :return:
        """
        for (k, v) in nic_to_subnet_map.items():
            if v == subnet_name:
                return k
        return None

    def _create_nic_to_subnet_name_map(self, network_client, instance, group_name):
        map = {}

        for nic_ref in instance.network_profile.network_interfaces:
            nic_name = self.resource_id_parser.get_name_from_resource_id(nic_ref.id)
            nic = network_client.network_interfaces.get(group_name, nic_name)
            ip_configuration = nic.ip_configurations[0]

            subnet_name = self.resource_id_parser.get_name_from_resource_id(ip_configuration.subnet.id)

            map[nic] = subnet_name

        return map

    @staticmethod
    def _create_security_group_action_result(app_name, is_success, message):
        result = SetAppSecurityGroupActionResult()
        result.appName = app_name
        result.success = is_success
        result.error = message
        return result
