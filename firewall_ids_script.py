from utils import *
import csv
import argparse

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

#pfsense_ami = 'pfsens-image-v1.0'
pfsense_ami = 'pfsense-image-v3.0'
win10_gw_ami = 'win10gw-image-v1.0'
win7_internal_ami = 'win7-image-v4.1'

def prov(num_instances, out_csvfile):

    # pfsense 
    pfsense_ami_id =  get_ami_id(pfsense_ami)
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

    instanceIdList = create_instances(pfsense_ami_id, 
                                subnet_secgrps_tuples, 
                                num_instances, 
                                auto_assign_public_ip=True, 
                                src_dst_chk=False,
                                size='t2.medium', rebootFlag=True)

    pfsense_infos = get_instances_info(instanceIdList)
    print(pfsense_infos)

    # win10_gw (public/private) 
    win10_gw_ami_id = get_ami_id(win10_gw_ami)
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

    instanceIdList = create_instances(win10_gw_ami_id, 
                                subnet_secgrps_tuples, 
                                num_instances, 
                                auto_assign_public_ip=True,
                                size='t2.medium')

    win10_gw_infos = get_instances_info(instanceIdList)
    print(win10_gw_infos)

    # win7 private (private) 
    win7_internl_ami_id = get_ami_id(win7_internal_ami)
    secgrpnames_private = ['win7rdpsmbsecuritygroup']  # private

    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(win7_internl_ami_id, 
                                    subnet_secgrps_tuples, 
                                    num_instances, 
                                    auto_assign_public_ip=False,
                                    size='t2.medium')
    win7_internal_infos = get_instances_info(instanceIdList)
    print(win7_internal_infos)

    # format csv
    combined_infos = zip(pfsense_infos, win10_gw_infos, win7_internal_infos)

    info_dict_list = []
    
    for index, (pfsense_info, win10_gw_info, win7_internal_info) in  enumerate(combined_infos):
        info_dict = {}
        info_dict['pfsense_instance_id'] = pfsense_info['id']
        info_dict['pfsense_public_ip'] = pfsense_info['public_ip']
        name = 'pfsense-' + str(index+1)
        tag_instance(info_dict['pfsense_instance_id'], name)
        for intf in pfsense_info['nets']:
            keyname = 'pfsense_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']

        info_dict['win10_gw_instance_id'] = win10_gw_info['id']
        info_dict['win10_gw_public_ip'] = win10_gw_info['public_ip']
        name = 'win10gw-' + str(index+1)
        tag_instance(info_dict['win10_gw_instance_id'], name)
        for intf in win10_gw_info['nets']:
            keyname = 'win10_gw_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']

        info_dict['win7_internal_instance_id'] = win7_internal_info['id'] 
        name = 'win7internal-' + str(index+1)
        tag_instance(info_dict['win7_internal_instance_id'], name)
        for intf in win7_internal_info['nets']:
            keyname = 'win7_internal_priv_ip#' + str(intf['intf_index'])
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
            instance_list.append(row['pfsense_instance_id'])
            instance_list.append(row['win10_gw_instance_id'])
            instance_list.append(row['win7_internal_instance_id'])
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

