# Steps to Convert VMWare workstation VMs to EC2 AMI

**Note** 
Make sure the VMWare VM to be converted is not using EFI partitioned drives or using UEFI boot loaders. 

**Note**
Step 1 and 2 below is only done once as part of the setup. For actual importing of images to EC2, perform only step 3.

To perform the conversion, you need to first setup a trusted role to do so

1. **Create a IAM service role**

You first need to create a service role using the [trust-policy.json](trust-policy.json) file.

Run this using the AWS CLI: 

```bash
aws iam create-role --role-name vmimport --assume-role-policy-document file://trust-policy.json
```

2. **Attach a policy to the role**

We then create a policy file [role-policy.json](role-policy.json), specifying the permissions on various s3 resources, including the bucket you are going to upload the .ova image to.  We attach the policy to the role we created in step 1:

```bash
aws iam put-role-policy --role-name vmimport --policy-name vmimport --policy-document file://role-policy.json
```

3. **Import the image to EC2**

Now we need to create a json file to describe the image format (e.g. OVA), and the location of the image (the key of the ova file in our bucket, e.g. windows10fromVMWare.ova). An example of the json file, [importova.json](importova.json) is given. 

Now you start the importing process: 

```bash
aws ec2 import-image --description "MyVM" --license-type BYOL --disk-containers file://importova.json
```

You should see something like the following screenshot, and pay attention to the status, it can be any of the following: active, converting, validating, booting, deleting, completed, etc. If you see it deleting, it means your image cannot be imported, bad luck !! 

```
{
    "Description": "MyVM",
    "ImportTaskId": "import-ami-0aab0d958efdbfc62",
    "LicenseType": "BYOL",
    "Progress": "0",
    "SnapshotDetails": [
        {
            "Description": "winddk",
            "DiskImageSize": 0.0,
            "Format": "OVA",
            "UserBucket": {
                "S3Bucket": "sdaai-team1",
                "S3Key": "windows10x64.ova"
            }
        }
    ],
    "Status": "active",
    "StatusMessage": "pending"
}
```

The conversion can take a while depending on the size of the image. 

You can monitor the progress of the conversion and importing to EC2 AMI using the following command: 

```
aws ec2 describe-import-image-tasks --import-task-ids import-ami-0aab0d958efdbfc62
```

You need to replace the import-task-ids with the id shown when you start the importing using the command ec2 import-image. In our case the image-task-ids is `import-ami-0aab0d958efdbfc62`

This id is also the id given to the AMI. So you go to the AMI listing page, you can look for this in the AMI ID column. 

# Conversion of hard disk volumes to EBS 
Make sure the virtual disk is using pre-allocated disk space option. Also specify RAW format in the import script




# Miscellaneous stuff 

## Create VPC manually

If you create a VPC manually, then you need to create an Internet Gateway and attach to the created VPC. Also you need to have a RouteTable that have the following:
1. Add the routes 0.0.0.0/0 (default route) and point to Internet Gateway created as target
2. Associate the route table to a subnet (e.g. public subnet of the VPC created)

