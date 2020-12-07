
import boto3
import os
from datetime import datetime, timedelta

sns = os.environ['sns_topic']
clusterid = os.environ['cluster_identifier']

# Main function Lambda will run at start
def lambda_handler(event, context):
    snapshot_deleted = redshift_snapshot_remover()
    snapshot_success = redshift_manual_snap()
    print("TEST123")
    if snapshot_deleted and snapshot_success:
        return "Completed"
    else:
        return "Failure"

# Function to connect to AWS services
def connect(service):
    print ('Connecting to AWS Service: ' + service)
    client = boto3.client(service)
    if client is None:
        msg = 'Connection to ' + service + 'failed in'
        notify_devops('Redshift manual snapshot Lambda function: FAILURE', msg)
    return client

# Function to take manual snapshot of the latest automated snapshot for each Redshift Cluster
def redshift_manual_snap():
    print ('Running function for Redshift manual snapshot copy')
    try:
        client = connect('redshift')
        client.create_cluster_snapshot(
                    SnapshotIdentifier = clusterid + '-snapshot-' + datetime.now().isoformat(timespec='microseconds').replace(":","-").replace(".","-") ,
                    ClusterIdentifier = clusterid)
                
        print ('The following manual snapshot was taken: ' + clusterid + '-snapshot-' + datetime.now().isoformat(timespec='microseconds').replace(":","-").replace(".","-"))
        notify_devops('Redshift manual snapshot Lambda function: SUCCESS', 'The following manual snapshot was taken: ' + clusterid + '-snapshot-' + datetime.now().isoformat(timespec='microseconds').replace(":","-").replace(".","-"))
        return True
    except Exception as e:
        print (str(e))
        notify_devops('Redshift manual snapshot Lambda function: FAILURE', str(e) + '. Please check Cloudwatch Logs')
        return False

# Function to remove manual snapshots which are older than specified in retention period variable
def redshift_snapshot_remover():
    print ('Running function to remove old snapshots')
    try:
        client = connect('redshift')
        snapshots = client.describe_cluster_snapshots(ClusterIdentifier=clusterid, SnapshotType='manual')
        snap = snapshots["Snapshots"]
        # Number of days to keep manual snapshots
        ret_period = os.environ['ret_period']
        # Maximum days to look back for manual snapshots to avoid deleting old snapshots still needed
        max_back = os.environ['max_back']
        del_snapshot = []
        
        removal_date = (datetime.now() - timedelta(days=int(ret_period))).date()
        max_look_back = (datetime.now() - timedelta(days=int(max_back))).date()
        # Looping through snap and removing snapshots which are older than retention period
        for s in snap:
            snap_date = s['SnapshotCreateTime'].date()
            # Condition for date older than retention period and condition to keep manual snapshots created by other person in the past
            if ((snap_date < removal_date) and (snap_date > max_look_back)):
                print ('Found snapshot older than retention period: ' + s['SnapshotIdentifier'] + '. Adding to the list.')
                del_snapshot.append(s['SnapshotIdentifier'])
                print ('Removing old snapshot: ' + s['SnapshotIdentifier'])
                client.delete_cluster_snapshot(
                    SnapshotIdentifier=s['SnapshotIdentifier'],
                    SnapshotClusterIdentifier=s['ClusterIdentifier']
                )
        deleted_snapshots = ', '.join(del_snapshot)
        if not deleted_snapshots:
            print ('No snapshots were found to be deleted')
            notify_devops('Deletion of old Redshift Snapshots: NO', 'No snapshots were found to be deleted')
        else:
            print ('List of deleted snapshots: ' + deleted_snapshots)
            notify_devops('Deletion of old Redshift Snapshots: YES', 'List of deleted snapshots: ' + deleted_snapshots)
        return True
    except Exception as e:
        print (str(e))
        notify_devops('Redshift manual snapshot Lambda function: FAILURE', str(e) + '. Please check Cloudwatch Logs')
        return False

# Function to notify DevOps team in case of a snapshot failure
def notify_devops(sub, msg):
    print ('Notifying DevOps team')
    client = connect('sns')
    pub_msg = client.publish(
        TopicArn = sns,
        Message = msg,
        Subject = sub
        )
    return pub_msg
