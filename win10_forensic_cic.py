from utils import *
import csv
import argparse

# Configuration:
# windows 10 in a single public subnet


vpc = 'vpc-cet'
subnet_public = 'Public subnet'

vpc_id = get_vpcId(vpc)
public_subnetid = get_subnetId(vpc_id, subnet_public)

win10forensic_ami = 'win10-forensic-image-v2.0'

def prov(num_instances, out_csvfile):

    # win10 (forensic) image 
    win10forensic_ami_id = get_ami_id(win10forensic_ami) 
    secgrpnames_public = ['allows_rdp_icmp_vpc-cet']  # public 

    public_secgrpIdlist = get_secgrpIds(secgrpnames_public)

    secgrpIdsList = []
    secgrpIdsList.append(public_secgrpIdlist)

    subnetIdList = []
    subnetIdList.append(public_subnetid)

    subnet_secgrps_tuples = zip(subnetIdList, secgrpIdsList)

    instanceIdList = create_instances(win10forensic_ami_id, 
                                      subnet_secgrps_tuples, 
                                      num_instances, 
                                      auto_assign_public_ip=True,
                                      size='t2.medium',
                                      mounted_vol='xvdf')

    tag_instances(instanceIdList, 'win10forensic')                                  
    win10forensic_infos = get_instances_info(instanceIdList)
    print(win10forensic_infos)


    # format csv
    info_dict_list = []
    
    for index, win_info in enumerate(win10forensic_infos):
        info_dict = {}
        info_dict['win10forensic_instance_id'] = win_info['id']
        info_dict['win10forensic_public_ip'] = win_info['public_ip']
        name = 'win10forensic-' + str(index+1)
        tag_instance(info_dict['win10forensic_instance_id'], name)
        for intf in win_info['nets']:
            keyname = 'win10forensic_priv_ip#' + str(intf['intf_index'])
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
            instance_list.append(row['win10forensic_instance_id'])
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

