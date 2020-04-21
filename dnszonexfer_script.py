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

win2016dc_ami_id = 'ami-0374e9267e2c3ff09'
kali2020_ami_id = 'ami-08d5b1b0f5ed7e5f5'


def prov(num_instances, out_csvfile):

    # Windows 2016 (public/private interface)

    # allow DNS (port 53) on private subnet only
    # allows RDP on public subnet
 
    secgrpnames_public = ['allow_rdp_vpc_demo']  # public 
    secgrpnames_private = ['allow_dns_vpc_demo']  # private

    public_secgrpIdlist = get_secgrpIds(secgrpnames_public)
    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(public_secgrpIdlist)
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(public_subnetid)
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(win2016dc_ami_id, subnet_secgrps_tuples, num_instances, auto_assign_public_ip=True, size='t2.large')
    
    win2016dc_infos = get_instances_info(instanceIdList)
    print(win2016dc_infos)

    # Kali 2020 (public private interface) 

    secgrpnames_public = ['allow_ssh_vpc_demo']  # public 
    secgrpnames_private = ['allow_ssh_vpc_demo']  # private

    public_secgrpIdlist = get_secgrpIds(secgrpnames_public)
    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(public_secgrpIdlist)
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(public_subnetid)
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(kali2020_ami_id, subnet_secgrps_tuples, num_instances, auto_assign_public_ip=True)
    
    kali_infos = get_instances_info(instanceIdList)
    print(kali_infos)

    

    # format csv
    combined_infos = zip(win2016dc_infos, kali_infos)

    info_dict_list = []
    
    for index, (win2016_info, kali_info) in enumerate(combined_infos):
        info_dict = {}
        info_dict['win2016dc_instance_id'] = win2016_info['id']
        info_dict['win2016dc_public_ip'] = win2016_info['public_ip']
        name = 'win2016dc-' + str(index+1)
        tag_instance(info_dict['win2016dc_instance_id'], name)
        for intf in win2016_info['nets']:
            keyname = 'win2016dc_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']
        info_dict['kali_instance_id'] = kali_info['id']
        info_dict['kali_public_ip'] = kali_info['public_ip']
        name = 'kali-' + str(index+1)
        tag_instance(info_dict['kali_instance_id'], name)
        for intf in kali_info['nets']:
            keyname = 'kali_priv_ip#' + str(intf['intf_index'])
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
            instance_list.append(row['win2016dc_instance_id'])
            instance_list.append(row['kali_instance_id'])
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

