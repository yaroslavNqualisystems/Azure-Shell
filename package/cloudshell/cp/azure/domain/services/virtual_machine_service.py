from azure.mgmt.compute.models import OSProfile, HardwareProfile, NetworkProfile, \
    NetworkInterfaceReference, CachingTypes, DiskCreateOptionTypes, VirtualHardDisk, ImageReference, OSDisk, \
    VirtualMachine, StorageProfile
from azure.mgmt.compute.models.linux_configuration import LinuxConfiguration
from azure.mgmt.compute.models.ssh_configuration import SshConfiguration
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.compute.models.ssh_public_key import SshPublicKey


class VirtualMachineService(object):
    def __init__(self):
        pass

    def get_vm(self, compute_management_client, group_name, vm_name):
        """

        :param compute_management_client:
        :param group_name:
        :param vm_name:
        :return: azure.mgmt.compute.models.VirtualMachine
        """

        return compute_management_client.virtual_machines.get(group_name, vm_name)

    def delete_vm(self,
                  compute_management_client,
                  resource_group_name,
                  vm_name):
        """
        :param compute_management_client:
        :param resource_group_name:
        :param vm_name:
        :return:
        """

        result = compute_management_client.virtual_machines.delete(resource_group_name, vm_name)

        return result.result()

    def _prepare_linux_configuration(self, ssh_key):
        """Create LinuxConfiguration object with nested SshPublicKey object for Azure client

        :param ssh_key: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        :return: azure.mgmt.compute.models.linux_configuration.LinuxConfiguration instance
        """
        ssh_public_key = SshPublicKey(path=ssh_key.path_to_key, key_data=ssh_key.key_data)
        ssh_config = SshConfiguration(public_keys=[ssh_public_key])

        return LinuxConfiguration(disable_password_authentication=True, ssh=ssh_config)

    def create_vm(self,
                  compute_management_client,
                  image_offer,
                  image_publisher,
                  image_sku,
                  image_version,
                  vm_credentials,
                  computer_name,
                  group_name,
                  nic_id,
                  region,
                  storage_name,
                  vm_name,
                  tags,
                  instance_type):
        """

        :param instance_type:
        :param compute_management_client:
        :param image_offer:
        :param image_publisher:
        :param image_sku:
        :param image_version:
        :param vm_credentials:
        :param computer_name:
        :param group_name:
        :param nic_id:
        :param region:
        :param storage_name:
        :param vm_name:
        :param tags:
        :return:
        """
        if vm_credentials.ssh_key:
            linux_configuration = self._prepare_linux_configuration(vm_credentials.ssh_key)
        else:
            linux_configuration = None

        os_profile = OSProfile(admin_username=vm_credentials.admin_username,
                               admin_password=vm_credentials.admin_password,
                               linux_configuration=linux_configuration,
                               computer_name=computer_name)

        hardware_profile = HardwareProfile(vm_size=instance_type)

        network_profile = NetworkProfile(network_interfaces=[NetworkInterfaceReference(id=nic_id)])

        vhd_format = 'https://{0}.blob.core.windows.net/vhds/{1}.vhd'.format(storage_name, vm_name)

        vhd = VirtualHardDisk(uri=vhd_format)

        os_disk = OSDisk(caching=CachingTypes.none,
                         create_option=DiskCreateOptionTypes.from_image,
                         name=storage_name,
                         vhd=vhd)

        image_reference = ImageReference(publisher=image_publisher, offer=image_offer, sku=image_sku,
                                         version=image_version)

        storage_profile = StorageProfile(os_disk=os_disk, image_reference=image_reference)

        virtual_machine = self._get_virtual_machine(hardware_profile,
                                                    network_profile,
                                                    os_profile,
                                                    region,
                                                    storage_profile,
                                                    tags)

        vm_result = compute_management_client.virtual_machines.create_or_update(group_name, vm_name, virtual_machine)

        return vm_result.result()

    def _get_virtual_machine(self, hardware_profile, network_profile, os_profile, region, storage_profile, tags):
        return VirtualMachine(location=region,
                              tags=tags,
                              os_profile=os_profile,
                              hardware_profile=hardware_profile,
                              network_profile=network_profile,
                              storage_profile=storage_profile)

    def create_resource_group(self, resource_management_client, group_name, region, tags):
        return resource_management_client.resource_groups.create_or_update(group_name,
                                                                           ResourceGroup(location=region, tags=tags))

    def delete_vm(self, compute_management_client, group_name, vm_name):
        """

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_management_client:
        :param group_name:
        :param vm_name:
        :return:
        """
        compute_management_client.virtual_machines.delete(resource_group_name=group_name,
                                                          vm_name=vm_name)

    def start_vm(self, compute_management_client, group_name, vm_name, async=False):
        """Start Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_management_client:
        :param group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :param async: (bool) whether wait for VM operation result or not
        :return:
        """
        operation_poller = compute_management_client.virtual_machines.start(resource_group_name=group_name,
                                                                            vm_name=vm_name)
        if not async:
            return operation_poller.result()

    def stop_vm(self, compute_management_client, group_name, vm_name, async=False):
        """Stop Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_management_client:
        :param group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :param async: (bool) whether wait for VM operation result or not
        :return:
        """
        operation_poller = compute_management_client.virtual_machines.power_off(resource_group_name=group_name,
                                                                                vm_name=vm_name)
        if not async:
            return operation_poller.result()
