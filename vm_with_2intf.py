import boto3
import time

#if_id = 'eni-09e4f0ad345810bc1'

ec2 = boto3.resource('ec2')

ami_id = 'ami-06be7fb41c22e3eaa'
sg_id = 'sg-055579f05ec4b29cf'



time.sleep(10)
print(instance.public_ip_address)


ec2_client.attach_network_interface(
    DeviceIndex = 1,
    InstanceId = instance.instance_id,
    NetworkInterfaceId = priv_if_id
)