from utils import *
import csv
import argparse

# Configuration:
# Kali with 2 interfaces in public and private subnet
# windows 10 (gateway) with 2 interfaces in public and private subnet
# win7 with 1 interface in private subnet (victim machine)

vpc = 'vpc_demo'
subnet_public = 'subnet1_demo'
subnet_private = 'subnet2_demo'

vpc_id = get_vpcId(vpc)
public_subnetid = get_subnetId(vpc_id, subnet_public)
private_subnetid  = get_subnetId(vpc_id,subnet_private)

kali_ami = 'kali2020-image-v1.4'
win10_gw_ami = 'win10gw-image-v1.0'
win7_victim_ami = 'win7-victim-image-v1.0'


win10_gw_ami_id = 'ami-0535e8383179a6d1f'
win7_victim_ami_id = 'ami-0a559734b59b0cb1c'

def prov(num_instances, out_csvfile):

    # kali
    kali_ami_id = get_ami_id(kali_ami)
    secgrpnames_public = ['allow_ssh_vpc_demo']  # public 
    secgrpnames_private = ['block_all_inbound_vpc_demo', 'allow_4444_5555_inbound_vpc_demo']  # private

    public_secgrpIdlist = get_secgrpIds(secgrpnames_public)
    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(public_secgrpIdlist)
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(public_subnetid)
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(kali_ami_id, 
                                subnet_secgrps_tuples, 
                                num_instances, 
                                auto_assign_public_ip=True,
                                size='t2.small')
                                
    kali_infos = get_instances_info(instanceIdList)
    print(kali_infos)

    # win10 gw (public/private) 
    win10_gw_ami_id = get_ami_id(win10_gw_ami)
    secgrpnames_public = ['allow_rdp_vpc_demo']  # public 
    secgrpnames_private = ['block_all_inbound_vpc_demo']  # private

    public_secgrpIdlist = get_secgrpIds(secgrpnames_public)
    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(public_secgrpIdlist)
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(public_subnetid)
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(win10_gw_ami_id, subnet_secgrps_tuples, num_instances, auto_assign_public_ip=True)
    win10_gw_infos = get_instances_info(instanceIdList)
    print(win10_gw_infos)

    # win7 victim (private) 
    win7_victim_ami_id = get_ami_id(win7_victim_ami)
    secgrpnames_private = ['allow_rdp_smb_vpc_demo']  # private

    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(win7_victim_ami_id, subnet_secgrps_tuples, num_instances, auto_assign_public_ip=False)
    win7_victim_infos = get_instances_info(instanceIdList) 
    print(win7_victim_infos)

    # format csv
    combined_infos = zip(kali_infos, win10_gw_infos, win7_victim_infos)

    info_dict_list = []
    
    for index, (pfsense_info, win10_gw_info, win7_victim_info) in enumerate(combined_infos):
        info_dict = {}
        info_dict['kali_instance_id'] = pfsense_info['id']
        name = 'kali-' + str(index+1)
        tag_instance(info_dict['kali_instance_id'], name)
        info_dict['kali_public_ip'] = pfsense_info['public_ip']
        for intf in pfsense_info['nets']:
            keyname = 'kali_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']

        info_dict['win10_gw_instance_id'] = win10_gw_info['id']
        name = 'win10gw-' + str(index+1)
        tag_instance(info_dict['win10_gw_instance_id'], name)
        info_dict['win10_gw_public_ip'] = win10_gw_info['public_ip']
        for intf in win10_gw_info['nets']:
            keyname = 'win10_gw_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']

        info_dict['win7_victim_instance_id'] = win7_victim_info['id']
        name = 'win7victim-' + str(index+1)
        tag_instance(info_dict['win7_victim_instance_id'], name)
        for intf in win7_victim_info['nets']:
            keyname = 'win7_victim_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']

        info_dict_list.append(info_dict)

    info_dict_sample = info_dict_list[0]
    keynames = info_dict_sample.keys()
    print('dumping info_dict_list')
    for info_dict in info_dict_list:
        print(info_dict)
    with open(out_csvfile, 'w', newline='') as csvfile:
        #fieldnames = info_dict.keys()
        writer = csv.DictWriter(csvfile, fieldnames=keynames)
        writer.writeheader()
        for info_dict in info_dict_list:
            print('writing row = {}'.format(info_dict))
            writer.writerow(info_dict)

def deprov(csvfile):
    with open(csvfile, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        instance_list = []
        for row in csv_reader:
            instance_list.append(row['kali_instance_id'])
            instance_list.append(row['win10_gw_instance_id'])
            instance_list.append(row['win7_victim_instance_id'])
        print('Deprovisioning {} instances'.format(len(instance_list)))
        delete_instances(instance_list)

parser = argparse.ArgumentParser(description='pfsense argument parser')
parser.add_argument("-d", help="Deprovisioning vms, specify the csv file, e.g. -d vms.csv")
parser.add_argument("-p", help="Provisioning vm, specify number of instances, e.g. -p 5")
parser.add_argument("-o", help="Output csv file, required for -d option, e.g. -p 5 -o vms.csv")

args = parser.parse_args()

if args.d: 
    csv_file = args.d 
    deprov(csv_file)
elif args.p:
    if not args.o:
        print('must specify output file using -o option')
        exit(-1)
    num_instances = int(args.p)
    out_csv = args.o
    prov(num_instances, out_csv)

