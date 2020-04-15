from utils import *

secgrpnames1 = ['win7rdp_vpc_demo_securitygroup', 'pfsense_vpcdemo']
secgrpnames2 = ['pfsense_vpcdemo']

secgrpIds1 = get_secgrpIds(secgrpnames1)
print(secgrpIds1)

secgrpIds2 = get_secgrpIds(secgrpnames2)
print(secgrpIds2)

secgrpIdsList = []
secgrpIdsList.append(secgrpIds1)
secgrpIdsList.append(secgrpIds2)
print('secgrpIdsList = ',secgrpIdsList)
vpc_id = get_vpcId('vpc_demo')

subnet1 = get_subnetId(vpc_id, 'subnet1_demo')
subnet2 = get_subnetId(vpc_id,'subnet2_demo')
print(subnet1, subnet2)
subnetIds = []
subnetIds.append(subnet1)
subnetIds.append(subnet2)



print(type(secgrpIdsList))
subnets_secgrps = zip(subnetIds, secgrpIdsList)

ami_id = 'ami-06be7fb41c22e3eaa'

#subnets_secgrps_list  = list(subnets_secgrps)
#print(subnet, secgrps)
# instance = create_instance(ami_id, subnets_secgrps)
# print(instance)
# print('remaining')
# x, y = subnets_secgrps_list[1]
# print(x, 'ssss', y)

instanceIdList = create_instances(ami_id, subnets_secgrps, 3)

instanceIdList = ['i-067eab86a1319162d', 'i-0d42b37b627eb8a76','i-0f9591c904689ac06']

get_instances_info(instanceIdList)