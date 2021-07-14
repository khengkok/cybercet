### Update your local repo with the updated version of utils.py 
The updated version of utils.py contains additional argument in describe_images() call, i.e. Owners.  This is to prevent getting duplicate image names as the shared ami from the OLD account also have the same image name. 

### Share AMI to new account 

In the OLD acccount:

- Right Click on the AMI you want to share and select "Modify  Image Permissions" 
- Type in the **NEW** account ID (e.g. XXXXX)
- Remember to check the box "Add create volumn permissions"

In the NEW account:
- Goto AMI page and in the list of AMI images, select Private Images and you should be able to see the AMI that you shared earlier
- Select the AMI and right click and select Copy AMI
- In the Copy AMI, make sure you select the same region as the OLD account (e.g. ap-southeast1/Asia Pacific (Singapore)) and click COPY AMI

### Create VPCs and associated subnets
the two VPCs: vpc-demo and vpc-cet have been re-created, and an internet-gw has been associated with each of them
the associated subnets have been recreated: 
vpc-demo:  subnet1_demo, subnet2_demo
vpc-cet: "Public subnet"
Routing tables have been configured for all these subnets. 

**Respective instructors please check if the routing works properly after you launch your VMs**
**If you have created other VPCs on your own in the OLD account, other than the above, please recreate it yourself.**


### Create security groups

Check your scripts for the required security groups. 
Search the security group in the OLD account and find out the following:
- what VPC it is attached to 
- rules (ports/ip address allowed)

Check if the security groups already created (maybe by others) in the NEW account. If not, create the security group using the information you collected above.


### AMIs that are from Marketplace 

Those AMIs from marketplace cannot be copied to new accounts and must be re-created. These include:
- Kali
- pfSense

Using the launch wizard, select the corresponding image from marketplace and launch the VM into an appropriate subnet, login, apply the changes, test it, and then stop the VM instance.  Right-click on stopped instance, and choose Create Image option and give your AMI the same name as your scripts so that you DON'T have to change the script. 

If there is any customization done on the marketplace images, **respective instructors need to apply the same changes to the new instances launched from Marketplace**

**Update: pfSense has been migrated to the new account, the respective instructor please test and make sure it continues to work**
