from utils import *
import csv

# Configuration:
# pfsense with 2 interfaces in public and private subnet
# win7#1 with 2 interfaces in public and private subnet
# win7#2 with 1 interface in private subnet

vpc = 'vpc_demo'
subnet_public = 'subnet1_demo'
subnet_private = 'subnet2_demo'

vpc_id = get_vpcId(vpc)
public_subnetid = get_subnetId(vpc_id, subnet_public)
private_subnetid  = get_subnetId(vpc_id,subnet_private)

num_instances = 2

# pfsense 
pfsense_ami_id = 'ami-0077821e284c5f18e'
secgrpnames_public = ['pfsense_vpcdemo']  # public 
secgrpnames_private = ['pfsense_vpcdemo']  # private

public_secgrpIdlist = get_secgrpIds(secgrpnames_public)
private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

secgrpIdsList = []
secgrpIdsList.append(public_secgrpIdlist)
secgrpIdsList.append(private_secgrpIdlist)

subnetIdList = []
subnetIdList.append(public_subnetid)
subnetIdList.append(private_subnetid)

subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

instanceIdList = create_instances(pfsense_ami_id, subnet_secgrps_tuples, num_instances)
pfsense_infos = get_instances_info(instanceIdList)
print(pfsense_infos)

# win7#1 (public/private) 
win7_1_ami_id = 'ami-021ad573e15d1bf7d'
secgrpnames_public = ['win7rdp_vpc_demo_securitygroup']  # public 
secgrpnames_private = ['win7rdp_vpc_demo_securitygroup']  # private

public_secgrpIdlist = get_secgrpIds(secgrpnames_public)
private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

secgrpIdsList = []
secgrpIdsList.append(public_secgrpIdlist)
secgrpIdsList.append(private_secgrpIdlist)

subnetIdList = []
subnetIdList.append(public_subnetid)
subnetIdList.append(private_subnetid)

subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

instanceIdList = create_instances(win7_1_ami_id, subnet_secgrps_tuples, num_instances, auto_assign_public_ip=True)
win7_1_infos = get_instances_info(instanceIdList)
print(win7_1_infos)

# win7#2 (private) 
win7_2_ami_id = 'ami-06be7fb41c22e3eaa'
secgrpnames_private = ['win7rdpsmbsecuritygroup']  # private

private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

secgrpIdsList = []
secgrpIdsList.append(private_secgrpIdlist)

subnetIdList = []
subnetIdList.append(private_subnetid)

subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

instanceIdList = create_instances(win7_2_ami_id, subnet_secgrps_tuples, num_instances, auto_assign_public_ip=False)
win7_2_infos = get_instances_info(instanceIdList)
print(win7_2_infos)

# format csv
combined_infos = zip(pfsense_infos, win7_1_infos, win7_2_infos)

info_dict_list = []
info_dict = {}
for pfsense_info, win7_1_info, win7_2_info in combined_infos:
    info_dict['pfsense_instance_id'] = pfsense_info['id']
    info_dict['pfsense_public_ip'] = pfsense_info['public_ip']
    for intf in pfsense_info['nets']:
        keyname = 'pfsense_priv_ip#' + str(intf['intf_index'])
        info_dict[keyname] = intf['priv_ip']
    info_dict['windows7_1_instance_id'] = win7_1_info['id']
    info_dict['windows7_1_public_ip'] = win7_1_info['public_ip']
    for intf in win7_1_info['nets']:
        keyname = 'windows7_1_priv_ip#' + str(intf['intf_index'])
        info_dict[keyname] = intf['priv_ip']
        info_dict['windows7_1_instance_id'] = win7_1_info['id']
    info_dict['windows7_2_instance_id'] = win7_2_info['id']
    #info_dict['windows7_2_public_ip'] = win7_1_info['public_ip']
    for intf in win7_2_info['nets']:
        keyname = 'windows7_2_priv_ip#' + str(intf['intf_index'])
        info_dict[keyname] = intf['priv_ip']

    info_dict_list.append(info_dict)

info_dict_sample = info_dict_list[0]
keynames = info_dict_sample.keys()
# for info_dict in info_dict_list:
#     print(info_dict)
with open('netinfo.csv', 'w', newline='') as csvfile:
    #fieldnames = info_dict.keys()
    writer = csv.DictWriter(csvfile, fieldnames=keynames)
    writer.writeheader()
    for info_dict in info_dict_list:
        writer.writerow(info_dict)