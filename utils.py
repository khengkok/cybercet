import boto3
import time
import json

ec2_client = boto3.client('ec2')
ec2 = boto3.resource('ec2')

POLLING_WAIT_INTERVAL = 3   # 3 seconds of waiting
SYSTEM_CHECK_INTERVAL = 3   # system check every 2 seconds
MAX_INSTANCE_READY_WAIT_TIME = 60  # 60 seconds 

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

def get_ami_id(image_name): 
    response = ec2_client.describe_images(
        Filters = [
            {
                'Name': 'name',
                'Values': [image_name]
            }
        ], 
        Owners = ['self']
    )
    # assume only 1 image matches the name
    images = response['Images']
    if len(images) > 1:
        raise Exception('more than 1 image matches the image name={}'.format(image_name))
    elif len(images) == 0:
        raise Exception('no image matches the image name={}'.format(image_name))
    return images[0]['ImageId']

def create_interface(subnet_id):
    response = ec2_client.create_network_interface(
                    SubnetId = subnet_id
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

def create_instances(ami_id, subnet_secgrp_tuples, num_instances, auto_assign_public_ip = True, size='t2.medium', mounted_vol=None, src_dst_chk=True, systemCheckFlag=False, rebootFlag=False, device_name='/dev/sda1'):
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
   
    devicemappings = []
    # add the default root volume 
    rootvol = {}
    rootvol['DeviceName'] = device_name
    rootvol['Ebs'] = {}
    rootvol['Ebs']['DeleteOnTermination'] = True
    
    devicemappings.append(rootvol)

    if mounted_vol != None: 
        mountvol = {}
        mountvol['DeviceName'] = mounted_vol
        mountvol['Ebs'] = {}
        mountvol['Ebs']['DeleteOnTermination'] = True
        devicemappings.append(mountvol)

    # create instance with volumes deleted when instance terminates
    instances = ec2.create_instances(
        BlockDeviceMappings = devicemappings,
        ImageId = ami_id,
        InstanceType = size,
        MaxCount = num_instances,
        MinCount = num_instances,
        NetworkInterfaces= netconfiglist,
        DryRun = False
    )
    
    instanceIdList = []
    for instance in instances: 
        instanceIdList.append(instance.instance_id)

    notReadyList = instanceIdList.copy()

    # wait for a while in case the instances are not ready to be described 
    time.sleep(5)
    
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
                        print('attaching if_id = {}, to instance_id = {}'.format(if_id, running_instance_id))
                        attach_response = ec2_client.attach_network_interface(
                            DeviceIndex = index,
                            InstanceId = running_instance_id,
                            NetworkInterfaceId = if_id
                        )
                        attachment_id = attach_response['AttachmentId']
                        ec2_client.modify_network_interface_attribute(
                            NetworkInterfaceId=if_id,
                            SourceDestCheck={
                                'Value': src_dst_chk
                            }
                        )
                    notReadyList.remove(running_instance_id)
            print('not ready list = {}'.format(notReadyList))  
        else:
            print('not ready {}'.format(instanceStatuses))
            time.sleep(POLLING_WAIT_INTERVAL)

    if systemCheckFlag: 
        print('performing system check')
        statusCheckOKList = instanceIdList.copy()

        maxCount = MAX_INSTANCE_READY_WAIT_TIME/SYSTEM_CHECK_INTERVAL
        count = 0
        while len(statusCheckOKList) != 0:
            response = ec2_client.describe_instance_status(
                    InstanceIds=statusCheckOKList
            )
            instanceStatuses = response['InstanceStatuses']
            for status in instanceStatuses: 
                running_instance_id = status['InstanceId']
                instanceStatus = status['InstanceStatus']['Status']
                systemStatus = status['SystemStatus']['Status']
                if instanceStatus == 'ok' and systemStatus == 'ok':
                    print('system check passed for {}'.format(running_instance_id))
                    statusCheckOKList.remove(running_instance_id)
                    print('system check yet to pass list = {}'.format(statusCheckOKList))  
                elif instanceStatus == 'impaired' or systemStatus == 'impaired':
                    print('system check failed for {}'.format(running_instance_id))
                    ec2_client.reboot_instances(InstanceIds = [running_instance_id])
                else:
                    print('check status for {} is instanceStatus={}, systemStatus={}'.format(running_instance_id, instanceStatus,systemStatus))
                    if count > maxCount: 
                        print('exceeded max wait time, system check considered failed for {}, so reboot'.format(running_instance_id))
                        ec2_client.reboot_instances(InstanceIds = [running_instance_id])

            print('will perform system check again in {} seconds'.format(SYSTEM_CHECK_INTERVAL))
            time.sleep(SYSTEM_CHECK_INTERVAL)
            count += 1
            
    # This is a workaround for situation where pfsense already booted before the network intf
    # is attached to the instance. As the pfsense cannot see the interface, it treated it as 
    # misconfigured interface, and go into a mode to wait for user to manually add VLAN, etc, and 
    # go into permanent 'wait for user to enter' mode, hence the instanceCheck failed, and internet reachibility is affected
    if rebootFlag: 
        rebootingList = instanceIdList.copy()
        print('reboot requested, rebooting all instances')
        ec2_client.reboot_instances(InstanceIds=rebootingList)

        while len(rebootingList) != 0:
            response = ec2_client.describe_instance_status(
                    InstanceIds=rebootingList
            )
            instanceStatuses = response['InstanceStatuses']
            for status in instanceStatuses: 
                running_instance_id = status['InstanceId']
                instanceState = status['InstanceState']['Name'] 
                instanceStatus = status['InstanceStatus']['Status']
                systemStatus = status['SystemStatus']['Status']
                if instanceState == 'running':
                    print('check status for {} is instanceStatus={}, systemStatus={}'.format(running_instance_id, instanceStatus,systemStatus))
                    rebootingList.remove(running_instance_id)
            time.sleep(SYSTEM_CHECK_INTERVAL)

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

def delete_instances(instanceIdList):
    response = ec2_client.describe_instances(
        InstanceIds = instanceIdList
    )
    net_info_to_delete = []
    #print('number of instances returned by describing = {}'.format(len(instances)))
    for reservation in response['Reservations']:
        instances = reservation['Instances']
        for instance in instances:    
            #print('checking interfaces of instance = {}'.format(instance['InstanceId']))
            net_infos = []
            for net_if in instance['NetworkInterfaces']:
                net_info = {}
                device_index = net_if['Attachment']['DeviceIndex']
                net_info['intf_index'] = device_index
                net_info['if_id'] = net_if['NetworkInterfaceId']
                net_info['attachment_id'] = net_if['Attachment']['AttachmentId']
                net_infos.append(net_info)
                #print('got interface id = {}'.format(net_info['if_id']))
            if len(net_infos) > 1:
                for net_info in net_infos:
                    # we only delete non-0 interface 
                    if net_info['intf_index'] != 0:
                        net_info_to_delete.append(net_info)
                        #print('net_if {} is non-zero intf, adding to delete'.format(net_info['if_id']))
                    # else:
                    #     print('net_if {} is intf 0, skipping'.format(net_info['if_id']))
            # else: 
            #     print('instance {} only has single interface, skip delete intf'.format(instance['InstanceId']))

    print('stopping instances...')
    ec2_client.stop_instances(InstanceIds = instanceIdList, Force=True)
    
    notStoppedList = instanceIdList.copy()
    # must wait until all instances terminated before deleting the network interfaces
    time.sleep(5)  # wait for a while before checking status.. to avoid wasted API call
    while len(notStoppedList) != 0:
        response = ec2_client.describe_instances(
                    InstanceIds=notStoppedList
        )
        to_stop_instances = response['Reservations'][0]['Instances']
        for inst in to_stop_instances:
            if inst['State']['Name'] == 'stopped':
                stopped_instance_id = inst['InstanceId']
                print('stopped id = {}'.format(stopped_instance_id))
                notStoppedList.remove(stopped_instance_id)
        print('instances waiting to stop = {}'.format(notStoppedList))
        time.sleep(5)

    ## now all instances are terminated, delete all the network interfaces
    # wait for a while before deleting interfaces... it is because sometime the assignment is 
    # is not released yet 
    
    time.sleep(5) 
    for net_info in net_info_to_delete: 
        print('detaching interface={}'.format(net_info['if_id']))
        response = ec2_client.detach_network_interface(AttachmentId=net_info['attachment_id'], Force=True)
        print('deleting interface={}'.format(net_info['if_id']))
        ec2_client.delete_network_interface(NetworkInterfaceId=net_info['if_id'])

    ## now terminate all instances
    ec2_client.terminate_instances(InstanceIds = instanceIdList)
    return 

def tag_instances(instanceIdList, name, cost_group='cybercet'):

    for index, instanceId in enumerate(instanceIdList):
        tagValue = name + '-' + str(index+1)
        tag_instance(instanceId, tagValue, cost_group)
        
            

def tag_instance(instanceId, name, cost_group='cybercet'):
    print('tagging {} with name = {} and cost group = {}'.format(instanceId, name, cost_group))
    response = ec2_client.create_tags(
            DryRun=False,
            Resources=[
                instanceId,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name
                },
                {
                    'Key': 'Group',
                    'Value': cost_group
                }
            ]
        )
        
    volumes = ec2_client.describe_volumes(
        Filters=[{'Name':'attachment.instance-id','Values':[instanceId]}]
    )
    for disk in volumes['Volumes']:
        #print(disk['VolumeId'], disk['VolumeType'], disk['Size'])
        response = ec2_client.create_tags(
            DryRun=False,
            Resources=[
                disk['VolumeId'],
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name
                },
                {
                    'Key': 'Group',
                    'Value': cost_group
                }
            ]
        )
