#!/usr/bin/python3

import boto3
from datetime import datetime, timedelta
import time
import sys
cloudwatch = boto3.resource('cloudwatch')
ec2 = boto3.resource('ec2')

instid =  str(sys.argv[1])
instance = ec2.Instance(instid)
instance.monitor()  # Enables detailed monitoring on instance (1-minute intervals)
time.sleep(360)     # Wait 6 minutes to ensure we have some data (can remove if not a new instance)

metric_iterator_CPU = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                            MetricName='CPUUtilization',
                                            Dimensions=[{'Name':'InstanceId', 'Value': instid}])



metric_iterator_DISKREAD = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                            MetricName='DiskReadOps',
                                            Dimensions=[{'Name':'InstanceId', 'Value': instid}])


metric_iterator_NET_IN = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                            MetricName='NetworkIn',
                                            Dimensions=[{'Name':'InstanceId', 'Value': instid}])

metric_CPU = list(metric_iterator_CPU)[0]    # extract first (only) element

metric_DISK_READ = list(metric_iterator_DISKREAD)[0]

metric_NET_IN = list(metric_iterator_NET_IN)[0]


response = metric_CPU.get_statistics(StartTime = datetime.utcnow() - timedelta(minutes=5),   # 5 minutes ago
                                 EndTime=datetime.utcnow(),                              # now
                                 Period=300,                                             # 5 min intervals
                                 Statistics=['Average'])

                                
response1 = metric_DISK_READ.get_statistics(StartTime = datetime.utcnow() - timedelta(minutes=5),   # 5 minutes ago
                                 EndTime=datetime.utcnow(),                              # now
                                 Period=300,                                             # 5 min intervals
                                 Statistics=['Sum'])

response2 = metric_NET_IN.get_statistics(StartTime = datetime.utcnow() - timedelta(minutes=5),   
                                 EndTime=datetime.utcnow(),                              
                                 Period=300,                                             
                                 Statistics=['Sum'])


print ("Average CPU utilisation:", response['Datapoints'][0]['Average'], response['Datapoints'][0]['Unit'])

print ("Sum of the Disk read operations:", response1['Datapoints'][0]['Sum'])

print ("Sum of the Network in :", response2['Datapoints'][0]['Sum'])

# print (response)   # for debugging only
