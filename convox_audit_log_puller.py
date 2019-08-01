#!/usr/bin/env python3
import boto3
import datetime
from boto3.dynamodb.conditions import Attr
import json
import csv
import argparse

def get_exec_audit_logs(start_date, end_date, path_filter):
  audit_lines = []
  start_period = "{0}.000000.000000000".format(start_date.strftime('%Y%m%d'))
  end_period = "{0}.999999.999999999".format(end_date.strftime('%Y%m%d'))
  if path_filter == "all_logs":
    expression = Attr('timestamp').between(start_period, end_period)
  else:
    expression = Attr('path').contains(path_filter)&Attr('timestamp').between(start_period, end_period)
  response = audit_table.scan(FilterExpression=expression)
  audit_lines.extend(response['Items'])
  while 'LastEvaluatedKey' in response:
    response = audit_table.scan(FilterExpression=expression, ExclusiveStartKey=response['LastEvaluatedKey'])
    audit_lines.extend(response['Items'])
  return audit_lines

def get_organization_mapping():
  organization_lines = []
  response = organization_table.scan()
  organization_lines.extend(response['Items'])
  while 'LastEvaluatedKey' in response:
    response = organization_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    organization_lines.extend(response['Items'])
  org_mapping = {}
  for org in organization_lines:
    org_mapping[org['id']] = org['name']
  return org_mapping

def get_rack_mapping():
  rack_lines = []
  response = rack_table.scan()
  rack_lines.extend(response['Items'])
  while 'LastEvaluatedKey' in response:
    response = rack_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    rack_lines.extend(response['Items'])
  rack_mapping = {}
  for rack in rack_lines:
    rack_mapping[rack['id']] = rack['name']
  return rack_mapping

def get_user_mapping():
  user_lines = []
  response = users_table.scan()
  user_lines.extend(response['Items'])
  while 'LastEvaluatedKey' in response:
    response = users_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    user_lines.extend(response['Items'])
  user_mapping = {}
  for user in user_lines:
    user_mapping[user['id']] = user['email']
  return user_mapping

def map_log_event_to_email(log_events, convox_host):
  org_map = get_organization_mapping()
  rack_map = get_rack_mapping()
  user_map = get_user_mapping()
  for event in log_events:
    event['playback_url'] = ""
    if event['path'].endswith("/exec"):
      if convox_host:
        event['playback_url'] = "https://{host}/grid/organizations/{org_id}/racks/{rack_id}/audit_logs/{event_id}/artifact/playback".format(host=convox_host, org_id=event['organization'], rack_id=event['rack'], event_id=event['id'])
      else:
        event['playback_url'] = "/grid/organizations/{org_id}/racks/{rack_id}/audit_logs/{event_id}/artifact/playback".format(org_id=event['organization'], rack_id=event['rack'], event_id=event['id'])
    event['organization'] = org_map[event['organization']]
    event['rack'] = rack_map[event['rack']]
    event['user'] = user_map[event['user']]
  return log_events

def json_out(filename, json_data, format="json"):
  if format == "csv":
    file = open(filename,'w+')
    csv_writer = csv.writer(file)
    header = json_data[0].keys()
    csv_writer.writerow(header)
    for row in json_data:
      csv_writer.writerow(row.values())
    file.close()
  elif format == "json":
    with open(filename, "w") as file_handler:
      json.dump(json_data, file_handler, indent=2)

if __name__ == "__main__":

  cmdparser = argparse.ArgumentParser(prog="convox_audit_log_puller.py")
  cmdparser.add_argument("-d", "--days", default="7", help="Number of days to go back into logs (default: 7)", type=int)
  cmdparser.add_argument("-p", "--path", default="exec", help="Specific convox path to filter by (default: exec)")
  cmdparser.add_argument("--profile", default="default", help="AWS profile name used to connect to dynamodb (default: default)")
  cmdparser.add_argument("--host", default=False, help="Hostname of convox console to built playback urls (default: None)")

  cmdargs = cmdparser.parse_args()
  session = boto3.session.Session(profile_name=cmdargs.profile)
  dynamodb = session.resource('dynamodb')
  audit_table = dynamodb.Table('console-private-audit-logs')
  organization_table = table = dynamodb.Table('console-private-organizations')
  rack_table = dynamodb.Table('console-private-racks')
  users_table = dynamodb.Table('console-private-users')

  end_date = datetime.date.today()
  start_date = end_date - datetime.timedelta(days=cmdargs.days)
  print("\033[92m[+] Collecting relevant log files\033[0m")
  exec_logs = get_exec_audit_logs(start_date, end_date, cmdargs.path)
  print("\033[92m[+] Formating log files\033[0m")
  formatted_logs =  map_log_event_to_email(exec_logs, cmdargs.host)
  filename = "convox_{path}_audit_{start}-{end}.csv".format(path=cmdargs.path, start=start_date.strftime('%Y%m%d'), end=end_date.strftime('%Y%m%d'))
  print("\033[92m[+] Generating output file {0}\033[0m".format(filename))
  json_out(filename, formatted_logs, "csv")
