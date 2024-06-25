#!/usr/bin/env python
# Tests for subnet calculator CFN resource

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from subnet_calculator_v1 import calculateSubnetCIDR
import pytest

AZs = 3
TGW_LABEL = 'TGW'

#######
# /24 #
#######

def test_24_1subnet_normal_01():
  vpc_network = '10.113.0.0/24'
  subnets = [
    {'Label': 'Private1', 'Prefix': '26'},
    {'Label': 'TGW', 'Prefix': '28'},  
  ]
  expected_response = {
    'Private1': ['10.113.0.0/26', '10.113.0.64/26', '10.113.0.128/26'],
    'TGW': ['10.113.0.208/28', '10.113.0.224/28', '10.113.0.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_24_1subnet_oversized_01():
  vpc_network = '10.113.0.0/24'
  subnets = [
    {'Label': 'Private1', 'Prefix': '25'},
    {'Label': 'TGW', 'Prefix': '28'},  
  ]
  with pytest.raises(Exception):
    response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  

def test_24_2subnet_normal_01():
  vpc_network = '10.113.0.0/24'
  subnets = [
      {'Label': 'Private1', 'Prefix': '27'},
      {'Label': 'Public', 'Prefix': '27'},
      {'Label': 'TGW', 'Prefix': '28'},
  ]
  expected_response = {
      'Private1': ['10.113.0.0/27', '10.113.0.32/27', '10.113.0.64/27'],
      'Public': ['10.113.0.96/27', '10.113.0.128/27', '10.113.0.160/27'],
      'TGW': ['10.113.0.208/28', '10.113.0.224/28', '10.113.0.240/28']
  }
  response = calculateSubnetCIDR(
      vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_24_3subnet_normal_01():
  vpc_network = '10.113.0.0/24'
  subnets = [
      {'Label': 'Private1', 'Prefix': '27'},
      {'Label': 'Private2', 'Prefix': '28'},
      {'Label': 'Public', 'Prefix': '28'},
      {'Label': 'TGW', 'Prefix': '28'},
  ]
  expected_response = {
      'Private1': ['10.113.0.0/27', '10.113.0.32/27', '10.113.0.64/27'],
      'Private2': ['10.113.0.96/28', '10.113.0.112/28', '10.113.0.128/28'],
      'Public': ['10.113.0.144/28', '10.113.0.160/28', '10.113.0.176/28'],
      'TGW': ['10.113.0.208/28', '10.113.0.224/28', '10.113.0.240/28']
  }
  response = calculateSubnetCIDR(
      vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response



#######
# /23 #
#######

def test_23_1subnet_normal_01():
  vpc_network = '10.113.0.0/23'
  subnets = [
    {'Label': 'Private1', 'Prefix': '25'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/25', '10.113.0.128/25', '10.113.1.0/25'],
    'TGW': ['10.113.1.208/28', '10.113.1.224/28', '10.113.1.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_23_2subnet_normal_01():
  vpc_network = '10.113.0.0/23'
  subnets = [
    {'Label': 'Private1', 'Prefix': '26'},
    {'Label': 'Public', 'Prefix': '26'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/26', '10.113.0.64/26', '10.113.0.128/26'],
    'Public': ['10.113.0.192/26', '10.113.1.0/26', '10.113.1.64/26'],
    'TGW': ['10.113.1.208/28', '10.113.1.224/28', '10.113.1.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_23_3subnet_normal_01():
  vpc_network = '10.113.0.0/23'
  subnets = [
    {'Label': 'Private1', 'Prefix': '26'},
    {'Label': 'Private2', 'Prefix': '27'},
    {'Label': 'Public', 'Prefix': '27'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/26', '10.113.0.64/26', '10.113.0.128/26'],
    'Private2': ['10.113.0.192/27', '10.113.0.224/27', '10.113.1.0/27'],
    'Public': ['10.113.1.32/27', '10.113.1.64/27', '10.113.1.96/27'],
    'TGW': ['10.113.1.208/28', '10.113.1.224/28', '10.113.1.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


#######
# /22 #
#######

def test_22_1subnet_normal_01():
  vpc_network = '10.113.0.0/22'
  subnets = [
    {'Label': 'Private1', 'Prefix': '24'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/24', '10.113.1.0/24', '10.113.2.0/24'],
    'TGW': ['10.113.3.208/28', '10.113.3.224/28', '10.113.3.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_22_2subnet_normal_01():
  vpc_network = '10.113.0.0/22'
  subnets = [
    {'Label': 'Private1', 'Prefix': '25'},
    {'Label': 'Public', 'Prefix': '25'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/25', '10.113.0.128/25', '10.113.1.0/25'],
    'Public': ['10.113.1.128/25', '10.113.2.0/25', '10.113.2.128/25'],
    'TGW': ['10.113.3.208/28', '10.113.3.224/28', '10.113.3.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_22_3subnet_normal_01():
  vpc_network = '10.113.0.0/22'
  subnets = [
    {'Label': 'Private1', 'Prefix': '25'},
    {'Label': 'Private2', 'Prefix': '25'},
    {'Label': 'Public', 'Prefix': '26'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/25', '10.113.0.128/25', '10.113.1.0/25'],
    'Private2': ['10.113.1.128/25', '10.113.2.0/25', '10.113.2.128/25'],
    'Public': ['10.113.3.0/26', '10.113.3.64/26', '10.113.3.128/26'],
    'TGW': ['10.113.3.208/28', '10.113.3.224/28', '10.113.3.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


#######
# /21 #
#######

def test_21_1subnet_normal_01():
  vpc_network = '10.113.0.0/21'
  subnets = [
    {'Label': 'Private1', 'Prefix': '23'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/23', '10.113.2.0/23', '10.113.4.0/23'],
    'TGW': ['10.113.7.208/28', '10.113.7.224/28', '10.113.7.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_21_2subnet_normal_01():
  vpc_network = '10.113.0.0/21'
  subnets = [
    {'Label': 'Private1', 'Prefix': '24'},
    {'Label': 'Public', 'Prefix': '24'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/24', '10.113.1.0/24', '10.113.2.0/24'],
    'Public': ['10.113.3.0/24', '10.113.4.0/24', '10.113.5.0/24'],
    'TGW': ['10.113.7.208/28', '10.113.7.224/28', '10.113.7.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_21_3subnet_normal_01():
  vpc_network = '10.113.0.0/21'
  subnets = [
    {'Label': 'Private1', 'Prefix': '24'},
    {'Label': 'Private2', 'Prefix': '24'},
    {'Label': 'Public', 'Prefix': '25'},
    {'Label': 'TGW', 'Prefix': '28'},
  ]
  expected_response = {
    'Private1': ['10.113.0.0/24', '10.113.1.0/24', '10.113.2.0/24'],
    'Private2': ['10.113.3.0/24', '10.113.4.0/24', '10.113.5.0/24'],
    'Public': ['10.113.6.0/25', '10.113.6.128/25', '10.113.7.0/25'],
    'TGW': ['10.113.7.208/28', '10.113.7.224/28', '10.113.7.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response



#######
# /20 #
#######

def test_20_1subnet_normal_01():
  vpc_network = '10.113.0.0/20'
  subnets = [
    {'Label': 'Private1', 'Prefix': '22'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/22', '10.113.4.0/22', '10.113.8.0/22'],
    'TGW': ['10.113.15.208/28', '10.113.15.224/28', '10.113.15.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_20_2subnet_normal_01():
  vpc_network = '10.113.0.0/20'
  subnets = [
    {'Label': 'Private1', 'Prefix': '23'},
    {'Label': 'Public', 'Prefix': '23'},
    {'Label': 'TGW', 'Prefix': '28'}, 
  ]
  expected_response = {
    'Private1': ['10.113.0.0/23', '10.113.2.0/23', '10.113.4.0/23'],
    'Public': ['10.113.6.0/23', '10.113.8.0/23', '10.113.10.0/23'],
    'TGW': ['10.113.15.208/28', '10.113.15.224/28', '10.113.15.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response


def test_20_3subnet_normal_01():
  vpc_network = '10.113.0.0/20'
  subnets = [
    {'Label': 'Private1', 'Prefix': '23'},
    {'Label': 'Private2', 'Prefix': '23'},
    {'Label': 'Public', 'Prefix': '24'},
    {'Label': 'TGW', 'Prefix': '28'},
  ]
  expected_response = {
    'Private1': ['10.113.0.0/23', '10.113.2.0/23', '10.113.4.0/23'],
    'Private2': ['10.113.6.0/23', '10.113.8.0/23', '10.113.10.0/23'],
    'Public': ['10.113.12.0/24', '10.113.13.0/24', '10.113.14.0/24'],
    'TGW': ['10.113.15.208/28', '10.113.15.224/28', '10.113.15.240/28']
  }
  response = calculateSubnetCIDR(vpc_network, subnets, azs=AZs, tgw_label=TGW_LABEL)
  assert expected_response == response
