# Steps to Convert VMWare workstation VMs to EC2 AMI

**Note** 
Make sure the VMWare VM to be converted is not using EFI partitioned drives or using UEFI boot loaders. 

# Conversion of hard disk volumes to EBS 
Make sure the virtual disk is using pre-allocated disk space option. Also specify RAW format in the import script

## Pre-requisites 

To perform the conversion, you need to first setup a trusted role to do so


## create VPC manually

If you create a VPC manually, then you need to create an Internet Gateway and attach to the created VPC. Also you need to have a RouteTable that have the following:
1. Add the routes 0.0.0.0/0 (default route) and point to Internet Gateway created as target
2. Associate the route table to a subnet (e.g. public subnet of the VPC created)

