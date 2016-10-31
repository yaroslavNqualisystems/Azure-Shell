class DeleteAzureVMOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service,
                 tags_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService network_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service
        self.tags_service = tags_service

    def delete_resource_group(self, resource_client, group_name):

        try:
            self.vm_service.delete_resource_group(resource_management_client=resource_client, group_name=group_name)
        except Exception as e:
            raise e

    def delete_sandbox_subnet(self, network_client, cloud_provider_model, resource_group_name):
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=cloud_provider_model.management_group_name,
                                                                                   tags_service=self.tags_service)
        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == resource_group_name),
                      None)
        if subnet is None:
            raise Exception("Could not find a valid subnet.")

        network_client.subnets.delete(cloud_provider_model.management_group_name, sandbox_virtual_network.name,
                                      subnet.name)

    def delete(self, compute_client, network_client, group_name, vm_name):
        """
        :param group_name:
        :param network_client:
        :param vm_name: the same as ip_name and interface_name
        :param compute_client:
        :return:
        """
        try:

            self.vm_service.delete_vm(compute_management_client=compute_client,
                                      group_name=group_name,
                                      vm_name=vm_name)

            self.network_service.delete_nic(network_client=network_client,
                                            group_name=group_name,
                                            interface_name=vm_name)

            self.network_service.delete_ip(network_client=network_client,
                                           group_name=group_name,
                                           ip_name=vm_name)

        except Exception as e:
            self.logger.info('Deleting Azure VM Exception...')
            raise e
