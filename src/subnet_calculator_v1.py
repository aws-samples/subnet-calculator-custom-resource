#!/usr/bin/env python3
# CloudFormation custom resource that calculates subnet CIDRs
# This can be run directly to test the function.

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import cfnresponse
import traceback
from ipaddress import IPv4Network
import logging
import json

logging.basicConfig(level=logging.INFO)


def calculateSubnetCIDR(vpc_network:str, subnets:dict, azs:int, tgw_label=None):
  '''
  Calculates the CIDRs for the given subnet names/prefixes

  Parameters:
    vpc_network: (str) VPC network in the format X.X.X.X/XX, eg. 10.123.0.0/24
    subnets: List of dict in the format:
      [
        {
          "Label": (str) "SubnetLabel1"
          "Prefix" (str) "XX" # eg. "24". String because that's what CFN returns.
        },
        {
          "Label": (str) "SubnetLabel2"
          "Prefix" (str) "XX" # eg. 25
        },
        ...
      ]
    azs: (int) Number of AZs, defaults to 3,
    tgw_label: (None/str) The label for /28 TGW subnets, which is placed at the end of the VPC CIDR.
               If you do not need the TGW subnets to be at the end of the VPC CIDR,
               set this to None (the default)

  Returns: Dict with:
    { 
      "SubnetLabel1": [
        "X.X.X.X/XX",
        "X.X.X.X/XX",
        "X.X.X.X/XX",
      ],
      "SubnetLabel2": [
        ...
      ]
      ...
    }
  '''

  response_payload = {}
  vpc = IPv4Network(vpc_network)
  # List to keep track of available network space
  avail_space = [vpc]
  # If the TGW is at the end, has_tgw keeps track of whether there is a TGW subnet:
  has_tgw = False

  # For the below algorithm to work, we need the bigger networks in front of the list:
  subnets.sort(key=lambda x: int(x['Prefix']))


  for subnet in subnets:
    label = subnet['Label']
    # Skip the TGW for now, this will be done at the end
    if tgw_label and label == tgw_label:
      has_tgw = True
      continue
    prefix = int(subnet['Prefix'])
    if prefix == 0:
      continue
    subnet_list = []
    for az in range(azs):
      found = False
      logging.debug(f'Available space is {avail_space}')
      for net in sorted(avail_space):
        try:
          # Check if this network can be split:
          split_nets = list(net.subnets(new_prefix=prefix))
          # If we didn't get an exception, it worked. Use the first entry:
          subnet_list.append(str(split_nets[0]))
          logging.debug(f'Adding {split_nets[0]}')
          # Replace rest of the entries with the split entries minus what we used:
          avail_space.remove(net)
          avail_space.extend(split_nets[1:])
          logging.debug(f'After adding, available space is now {avail_space}')
          found = True
          break
        except ValueError:
          logging.debug(f'Could not split nework.')
          pass
      if not found:
        raise Exception('No more space in given network')
      response_payload[label] = subnet_list

  # If tgw_label was set, the TGW needs to be at the end of the VPC. 
  # Make sure there is space for it:
  if tgw_label and has_tgw:
    # Calculate the last 3 /28s in the VPC:
    tgw_subnets = list(vpc.subnets(new_prefix=28))[-3:]
    # Check to see if each fits in the available space:
    for tgw_subnet in tgw_subnets:
      tgw_fits = False
      for net in sorted(avail_space):
        if net.supernet_of(tgw_subnet):
          tgw_fits = True
          break
      if not tgw_fits:
        raise Exception(f'Could not fit TGW network {tgw_subnet}.')
    # Add the TGW subnet to the response:
    response_payload[tgw_label] = [str(subnet) for subnet in tgw_subnets]

  logging.info(f'Returning {response_payload}')

  return response_payload


def handler(event, context):
  print(f'event is {event}')
  # Load CFN resource details from SNS:
  msg = json.loads(event['Records'][0]['Sns']['Message'])
  properties = msg['ResourceProperties']

  response_payload = {}
  response_status = cfnresponse.FAILED
  physical_resource_id = 'unset'
  reason = None

  try:
    if msg['RequestType'] == 'Delete':
      # Nothing to delete:
      response_status = cfnresponse.SUCCESS
      
    elif msg['RequestType'] in ('Create','Update'):
      vpc_network = properties['VPCNetwork']
      physical_resource_id = f'subnet-calc-{vpc_network}'
      azs = int(properties.get('AZs', '3'))
      # List of {Label, Prefix} dicts:
      subnets = properties['Subnets']
      response_payload = calculateSubnetCIDR(vpc_network, subnets, azs, tgw_label='TGW')
      response_status = cfnresponse.SUCCESS

  except Exception as e:
    print('ERROR: Caught exception:')
    print(e)
    reason = str(e)
    traceback.print_exc()
  finally:
    print('Sending cfn response')
    cfnresponse.send(msg, context, response_status,
                     response_payload, physical_resource_id, reason=reason)


# Interactive test:
if __name__ == '__main__':
  vpc_network = '10.113.0.0/24'
  subnets = [
    {'Label': 'Private1', 'Prefix': "26"},
    {'Label': 'TGW', 'Prefix': '28'},  
  ]
  print( calculateSubnetCIDR(vpc_network, subnets, azs=3, tgw_label='TGW') )
  
