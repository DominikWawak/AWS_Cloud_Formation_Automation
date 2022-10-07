#!/usr/bin/env python3

import boto3
import os.path
import uuid
import webbrowser
import subprocess
import sys
import time

from os import path
from botocore.exceptions import ClientError

from operator import itemgetter


#************************************************ ASSIGNMENT 1 DEV OPS ********************************************#
#
#                                               Dominik Wawak
#                                               20089042
#***************************************************************************************************************#

ec2 = boto3.resource('ec2')

ec2_client = boto3.client('ec2')

s3 = boto3.resource("s3")
s3_client = boto3.client('s3')

#SIMPLE NOTIFICATION SERVICE
sns_client = boto3.client("sns")

bucket_name = 'webs2933'

#************************************************VARIABLES********************************************#
inst_id = ""

ip_address =""

keyName=""

#************************************************ Create Key Method ********************************************#
def create_key(keyString):
        print("Creating the key")
        print()
        #outfile = open('Dominik.pem','w')

        key_pair = ec2_client.create_key_pair(KeyName=keyString)

        private_key = key_pair["KeyMaterial"]

        global keyName
        keyName=keyString

        #Write the key to a file

        with os.fdopen(os.open(keyString+".pem", os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
                handle.write(private_key)
        #KeyPairOut = str(key_pair.key_material)
        #print(KeyPairOut)
        #outfile.write(KeyPairOut)
    


#
# creating a key programatically and saving it in a file:
# taken from https://blog.ipswitch.com/how-to-create-an-ec2-instance-with-python
#***********************************************************************************

#Check if key pair already exists
def checkKeyPair(keyName):
    keys = ec2_client.describe_key_pairs()
    flag=True

    for key in range(0,len(keys["KeyPairs"])-1):
        # print(keyName, keys["KeyPairs"][key]["KeyName"])
        if keyName == keys["KeyPairs"][key]["KeyName"]:
            flag=False
        
    return flag


print()

#************************************************ Check for arguments to create a key ********************************************#

# Check if there are any arguments passed in,
# if none create a default key
if(len(sys.argv) <= 1):
    if(os.path.isfile('Dominik.pem') or not checkKeyPair('Dominik.pem')):
        keyName='Dominik'
    else:
        create_key("Dominik")

    print("Key Name is " + str(keyName))

else:
    # if file name already exists  use that file,
    # otherwise create a key with the specified name
    if(os.path.isfile(str(sys.argv[1])+'.pem') or not checkKeyPair(str(sys.argv[1])) ):
        print(str(sys.argv[1]))
        print("Using Existing key")
        print("Key Pair already exists")
        keyName = sys.argv[1]
    else:
            print("Creating a key for you...")
       
            create_key(str(sys.argv[1]))
   
            
         



#***********************************************************************************

# CREATE SECURITY GROUP : 
# Taken from the boto3 API

#**********************************************************************************

response = ec2_client.describe_vpcs()
#vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
#Specify the vpc 
vpc_id = "vpc-06db3536c7fee80d4"
security_group_id =""

#Check if security gropu exists


print()

try:
    print("checking for security groups")
    response = ec2_client.describe_security_groups(GroupNames=['SECURITY_GROUP_BOTO'])
    print("Security group exists")
    print()
    print("Security group id is : ",response['SecurityGroups'][0]['GroupId'])
    if(response == None):
        try:
            print("Creating security group")
            response = ec2_client.create_security_group(GroupName='SECURITY_GROUP_BOTO' ,
                                                Description='MADE_WITH_PYTHON',
                                                VpcId=vpc_id)
            security_group_id = response['GroupId']
            print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

            data = ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                    {'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                    
                ])
            print('Ingress Successfully Set %s' % data)
        except ClientError as e:
            print(e)
    
    else:
        security_group_id = response['SecurityGroups'][0]['GroupId']

    
except ClientError as e:
    print(e)




#---------------OR--------------------

#securityGroup = ec2.create_security_group(GroupName='Boto3TestGroup', Description = 'Created In Python', VpcId='vpc-069027c552c3727d7')

#**********************************************************************************

#************************************************ User data script for instance to start and instal essentail items ********************************************#
user_data = '''
#!/bin/bash
echo 'Hello User!'

sudo -y yum update  

#install PHP
sudo yum -y install python-simplejson  
#install java
sudo yum install -y default-jre 

yum -y install httpd
systemctl enable httpd
service httpd start

#install mysql
yum install php php-mysql
service httpd restart
yum -y install mysql-server


echo "<?php echo '<p>Hello World</p>'; ?>" >> test.php



echo '<html>' > index.html
echo 'Private IP address: ' >> index.html
curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html 
echo " Public IP address" >> index.html
curl http://169.254.169.254/latest/meta-data/public-ipv4 >> index.html 
echo " Availability Zone " >> index.html
curl http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html 
echo " Security Groups " >> index.html
curl http://169.254.169.254/latest/meta-data/security-groups >> index.html
echo " ami-id: " >> index.html
curl http://169.254.169.254/latest/meta-data/ami-id >> index.html

echo " " >> index.html
cp index.html /var/www/html/index.html

cp test.php /var/www/html/test.php



'''


#************************************************ Get the latest AMI ****************************************#

# Found on stack overflow https://stackoverflow.com/questions/51611411/get-latest-ami-id-for-aws-instance

#Specify filters to make the search quicker for the lates ami

filters = [ {
    'Name': 'name',
    'Values': ['amzn-ami-hvm-*']
},{
    'Name': 'description',
    'Values': ['Amazon Linux AMI*']
},{
    'Name': 'architecture',
    'Values': ['x86_64']
},{
    'Name': 'owner-alias',
    'Values': ['amazon']
},{
    'Name': 'owner-id',
    'Values': ['137112412989']
},{
    'Name': 'state',
    'Values': ['available']
},{
    'Name': 'root-device-type',
    'Values': ['ebs']
},{
    'Name': 'virtualization-type',
    'Values': ['hvm']
},{
    'Name': 'hypervisor',
    'Values': ['xen']
},{
    'Name': 'image-type',
    'Values': ['machine']
} ]

response = ec2_client.describe_images(
  Filters=filters,
  Owners=[
      'amazon'
  ]
)


# Sort the image datails to get the most recent one
image_details = sorted(response['Images'],key=itemgetter('CreationDate'),reverse=True)
ami_id = image_details[0]['ImageId']



#************************************************* Create Instance ***********************************************#
print()
print("Creating Instance")
instance = ec2.create_instances(

 ImageId=ami_id,
 MinCount=1,
 MaxCount=1,
 InstanceType='t2.nano',
 SecurityGroupIds=[security_group_id],
 UserData=user_data,
 KeyName=keyName,
 TagSpecifications=[
        {
        "ResourceType":"instance",
        "Tags": [
                {
                    "Key": "Name",
                    "Value": "EC2_BOTO_TEST"
                }
            ]
    }
   ] 
    	
 )
print ("Instance being created the id is:   " +instance[0].id)






#************************************************ S3 Bucket Config ********************************************#
#
# Creates a intex.html file
# Creates website configurations and lauches a bucket,
# gets the image from a url with subprocess and puts them in a bucket.
# webbrowser opens the image.
#************************************************ S3 Bucket Config ********************************************#
instance[0].wait_until_running()
instance[0].reload()
ip_address = instance[0].public_ip_address

print("Opening the meta data website")
# webbrowser.open_new_tab('http://' + str(ip_address))
webbrowser.open_new_tab('http://' + str(ip_address)+'/index.html')





print()
print("Finished Launching Instance, Launching Bucket...")
print()

#check if an index.thml file exists to be uploaded onto the bucket if not create one.

if(not os.path.isfile('index.html')):


    print("Creating index.html")
    print()
    outfile = open('index.html','w')

    index_html = '''
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    img { 
    width: 100%; 
    }
    </style>
    </head>
    <body>
    <img src="https://webs2933.s3.eu-west-1.amazonaws.com/witImage.jpg" alt="HTML5 Icon">
    </body>
    </html>    
    '''


    
    outfile.write(index_html)
    outfile.close()


if not s3.Bucket(str(bucket_name)) in s3.buckets.all():


            website_configuration = {
                'ErrorDocument': {'Key': 'error.html'},
                'IndexDocument': {'Suffix': 'index.html'},
            }
            get_image = "curl -O http://devops.witdemo.net/assign1.jpg "
            subprocess.run(get_image , shell=True)

            try:
                    response = s3.create_bucket(
                        Bucket=bucket_name, 
                        CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'},
                        ACL='public-read'
                        )
                    
                    response = s3_client.put_bucket_tagging(
                    Bucket=bucket_name,
                    Tagging={
                        'TagSet': [
                            {
                                'Key': 'S3WITIMAGE',
                                'Value': 'img'
                            },
                        ]
                    },
                    ExpectedBucketOwner='793284281193'
                )
                    
                    s3_client.put_bucket_website(Bucket=bucket_name,WebsiteConfiguration=website_configuration)
                    s3_client.upload_file('assign1.jpg',bucket_name,'witImage.jpg',ExtraArgs={'ACL':'public-read'})
                    s3_client.upload_file('index.html',bucket_name,'index.html',ExtraArgs={'ContentType': 'text/html','ACL':'public-read'})


                    #print (response)

                    

                    
            except Exception as error:
                    print (error)
else:
    print("BUCKET ALREADY EXISTS")
    


#Get the endpoint URL
location = boto3.client('s3').get_bucket_location(Bucket=bucket_name)['LocationConstraint']
url = "http://%s.s3-website-%s.amazonaws.com" % (bucket_name,location)
print(url)
webbrowser.open_new_tab(url)

#************************************************************************************************************************#
 
sns_client.publish(PhoneNumber="+353899768146",Message="Hello its AWS your instance is running and your bucket is made!")



#for inst in ec2.instances.all():
#    print(inst.id,inst.public_ip_address,inst.state)


#************************************************ SSH into instance and copy over the monitor.sh script and run it ********************************************#


print("Running The monitor script")


scp_command = "scp -o StrictHostKeyChecking=no -i "+keyName+".pem monitor.sh ec2-user@"+ip_address+":. | chmod 700 monitor.sh "
ssh_command="ssh -o StrictHostKeyChecking=no -i "+keyName+".pem ec2-user@" + ip_address + " './monitor.sh' "
subprocess.run(scp_command,shell=True)
subprocess.run(ssh_command,shell=True)


# Cloud watch option
cloudWatch = input("Do you want to start cloud watch? ")

if str(cloudWatch).upper() == "YES" or str(cloudWatch).upper() == "Y":
    os.system('python3 cloudWatch.py ' + instance[0].id)


#Close program option 


close = input("Do you want to terminate and delete the bucket? ")
if str(close).upper() == "YES" or str(close).upper() == "Y":
    print("Closing in 20 Seconds")
    time.sleep(20)



    s3.Bucket(bucket_name).objects.all().delete()
    s3.Bucket(bucket_name).delete()
    instance[0].terminate()




#************************************************ END OF PROGRAM ********************************************#
