from utils import *
import csv
import argparse

# Configuration:
# win10 with 2 interfaces in public and private subnet
# win10 with 1 interface in private subnet (malware machine)

vpc = 'vpc_demo'
subnet_public = 'subnet1_demo'
subnet_private = 'subnet2_demo'

vpc_id = get_vpcId(vpc)
public_subnetid = get_subnetId(vpc_id, subnet_public)
private_subnetid  = get_subnetId(vpc_id,subnet_private)

win10_gw_ami = 'win10gw-image-v1.0'
win10_malware_ami = 'win10-malwan-flarevm-workshop-v2.0'

def prov(num_instances, out_csvfile):

    # windows public gateway with 1 public and 1 private network interface
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

    instanceIdList = create_instances(win10_gw_ami_id, 
                            subnet_secgrps_tuples, num_instances, 
                            auto_assign_public_ip=True,
                            size='t2.medium')

    win10_gw_infos = get_instances_info(instanceIdList)
    print(win10_gw_infos)

    # win10 malware (private interface only) 
    win10_malware_ami_id = get_ami_id(win10_malware_ami)
    secgrpnames_private = ['allow_inbound_rdp_block_all_outbound_vpc_demo']  # security grp for win10 malware vm private interface 

    private_secgrpIdlist = get_secgrpIds(secgrpnames_private)

    secgrpIdsList = []
    secgrpIdsList.append(private_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(private_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(win10_malware_ami_id, 
                            subnet_secgrps_tuples, 
                            num_instances, 
                            auto_assign_public_ip=False,
                            size='t2.medium')
                            
    win10_malware_infos = get_instances_info(instanceIdList)
    print(win10_malware_infos)


    # format csv
    combined_infos = zip(win10_gw_infos, win10_malware_infos)

    info_dict_list = []
    
    for index, (win10gw_info, win10malware_info) in enumerate(combined_infos):
        info_dict = {}
        info_dict['win10_gw_instance_id'] = win10gw_info['id']
        info_dict['win10_gw_public_ip'] = win10gw_info['public_ip']
        name = 'win10gw-' + str(index+1)
        tag_instance(info_dict['win10_gw_instance_id'], name)
        for intf in win10gw_info['nets']:
            keyname = 'win10_gw_priv_ip#' + str(intf['intf_index'])
            info_dict[keyname] = intf['priv_ip']
        info_dict['win10_malware_instance_id'] = win10malware_info['id']
        name = 'win10malware-' + str(index+1)
        tag_instance(info_dict['win10_malware_instance_id'], name)
        for intf in win10malware_info['nets']:
            keyname = 'win10_malware_priv_ip#' + str(intf['intf_index'])
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
            instance_list.append(row['win10_gw_instance_id'])
            instance_list.append(row['win10_malware_instance_id'])
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

