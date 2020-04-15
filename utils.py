import boto3
import time
import json

ec2_client = boto3.client('ec2')
ec2 = boto3.resource('ec2')

POLLING_WAIT_INTERVAL = 3   # 3 seconds of waiting

def get_secgrpIds(secgrpnames):
    response = ec2_client.describe_security_groups(
                Filters=[
                    {
                        'Name': 'group-name',
                        'Values': secgrpnames
                    }
                    
                ]
    )
    secgrpIds = []
    for secgrp in response['SecurityGroups']:
        secgrpIds.append(secgrp['GroupId'])
    
    return secgrpIds

def get_vpcId(vpcname): 
    response = ec2_client.describe_vpcs()
    for vpc in response['Vpcs']: 
        if vpc['Tags']: 
            for tag in vpc['Tags']: 
                if tag['Key'] == 'Name':
                    if tag['Value'] == vpcname: 
                        return vpc['VpcId']
    return None

def get_subnetId(vpc_id, subnetname):
    response = ec2_client.describe_subnets(
        Filters=[
        {
            'Name': 'vpc-id',
            'Values': [
                vpc_id,
            ]
        },
        ]
    )
    # print(response)
    for subnet in response['Subnets']: 
        for tag in subnet['Tags']:
            if tag['Key'] == 'Name': 
                if tag['Value'] == subnetname:
                    return subnet['SubnetId']
    return None

def create_interface(subnet_id):
    response = ec2_client.create_network_interface(
                    SubnetId = private_subnet_id
                )
    if_id = response['NetworkInterface']['NetworkInterfaceId']
    if_ip = response['NetworkInterface']['PrivateIpAddresses'][0]['PrivateIpAddress']
    return if_id, if_ip

def allocate_attach_eip(if_id):
    # allocate elastic IP
    response = ec2_client.allocate_address(
        Domain='vpc',
        DryRun=False
    )
    eip = response['PublicIp']
    allocid = response['AllocationId']
    
    print('type of allocid = {}, value = {}'.format(type(allocid), allocid))
    # associate with the given network interface
    response = ec2_client.associate_address(
        NetworkInterfaceId = if_id,
        AllocationId = allocid
    )
    associd = response['AssociationId']

    return eip, associd

def create_single_instance(ami_id, subnet_secgrp_tuples):
    netconfiglist = []

    # assume 1st one is for public 
    subnet_secgrp_list = list(subnet_secgrp_tuples)
    public_subnet, public_secgrps = subnet_secgrp_list[0]
    public_netconfig = {}
    public_netconfig['AssociatePublicIpAddress'] = True
    public_netconfig['DeviceIndex'] = 0
    public_netconfig['SubnetId'] = public_subnet
    public_netconfig['Groups'] = public_secgrps
 
    netconfiglist = []
    netconfiglist.append(public_netconfig)
   
    
    instances = ec2.create_instances(
        ImageId = ami_id,
        InstanceType = 't2.small',
        MaxCount = 1,
        MinCount = 1,
        NetworkInterfaces= netconfiglist,
        DryRun = False
    )
    
    instanceId = instances[0].instance_id
    print('launching instance id = {}'.format(instanceId))
    while True:
        response = ec2_client.describe_instance_status(
                InstanceIds=[instanceId])
        print(response)
        if response['InstanceStatuses']:
            if response['InstanceStatuses'][0]['InstanceState']['Name'] == 'running':
                break
        else:
            time.sleep(5)

    for index, (subnet, secgrplist) in enumerate(subnet_secgrp_list): 
        print('index = {}, subnet = {}, secgrplist = {}', index, subnet, secgrplist)

        if index == 0:
            continue
        response = ec2_client.create_network_interface(
            Groups = secgrplist,
            SubnetId = subnet
        )
        if_id = response['NetworkInterface']['NetworkInterfaceId']
        print('attacing if_id = {}, to instance_id = {}', if_id, instanceId)
        ec2_client.attach_network_interface(
            DeviceIndex = index,
            InstanceId = instanceId,
            NetworkInterfaceId = if_id
        )
    
    return instances[0]

def create_instances(ami_id, subnet_secgrp_tuples, num_instances, auto_assign_public_ip = True):
    netconfiglist = []

    # assume 1st one is for public 
    subnet_secgrp_list = list(subnet_secgrp_tuples)
    public_subnet, public_secgrps = subnet_secgrp_list[0]
    public_netconfig = {}
    public_netconfig['AssociatePublicIpAddress'] = auto_assign_public_ip
    public_netconfig['DeviceIndex'] = 0
    public_netconfig['SubnetId'] = public_subnet
    public_netconfig['Groups'] = public_secgrps
 
    netconfiglist = []
    netconfiglist.append(public_netconfig)
   
    
    instances = ec2.create_instances(
        ImageId = ami_id,
        InstanceType = 't2.small',
        MaxCount = num_instances,
        MinCount = num_instances,
        NetworkInterfaces= netconfiglist,
        DryRun = False
    )
    
    instanceIdList = []
    for instance in instances: 
        instanceIdList.append(instance.instance_id)

    notReadyList = instanceIdList.copy()

    while len(notReadyList) != 0:
        response = ec2_client.describe_instance_status(
                InstanceIds=notReadyList
        )
        instanceStatuses = response['InstanceStatuses']
        if instanceStatuses:   # some are ready
            for status in instanceStatuses: 
                if status['InstanceState']['Name'] == 'running':
                    running_instance_id = status['InstanceId']
                    for index, (subnet, secgrplist) in enumerate(subnet_secgrp_list): 
                        print('index = {}, subnet = {}, secgrplist = {}', index, subnet, secgrplist)
                        if index == 0:
                            continue
                        create_net_response = ec2_client.create_network_interface(
                            Groups = secgrplist,
                            SubnetId = subnet
                        )
                        if_id = create_net_response['NetworkInterface']['NetworkInterfaceId']
                        print('attacing if_id = {}, to instance_id = {}'.format(if_id, running_instance_id))
                        ec2_client.attach_network_interface(
                            DeviceIndex = index,
                            InstanceId = running_instance_id,
                            NetworkInterfaceId = if_id
                        )
                    notReadyList.remove(running_instance_id)
            print('not ready list = {}'.format(notReadyList))  
        else:
            print('not ready {}'.format(instanceStatuses))
            time.sleep(POLLING_WAIT_INTERVAL)

    return instanceIdList

def get_instances_info(instanceIdList):
    response = ec2_client.describe_instances(
        InstanceIds = instanceIdList
    )
    instances = response['Reservations'][0]['Instances']
    infos = []
    for instance in instances:
        inst_id = instance['InstanceId']
        if 'PublicIpAddress' in instance:
            public_ip = instance['PublicIpAddress']
        else:
            public_ip = None
        info = {}
        info['id'] = inst_id
        info['public_ip'] = public_ip
        net_infos = []
        for net_if in instance['NetworkInterfaces']:
            net_info = {}
            device_index = net_if['Attachment']['DeviceIndex']
            priv_ip = net_if['PrivateIpAddress']
            # print('device_index = {},  priv_ip = {}'.format(device_index, priv_ip))
            net_info['intf_index'] = device_index
            net_info['priv_ip'] = priv_ip
            net_infos.append(net_info)
        info['nets'] = sorted(net_infos, key = lambda e : e['intf_index'])
        infos.append(info)
    return infos

      