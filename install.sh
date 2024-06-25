#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
set -eu
template_file="subnet-calculator.yaml"
tmp_param_file="/tmp/subnet-calculator.param"

echo "Make sure you are running this in the Network account/AWS CLI profile"

# Write the OrgID parameter:
org_id=$(aws organizations describe-organization --query Organization.Id --output text)

if [[ -z "$org_id" ]]; then
  echo 'Error: could not get AWS organization ID'
  exit 1
fi

echo "OrgID=$org_id" > $tmp_param_file
./cfn_apply.sh Subnet-Calculator "$template_file" "$tmp_param_file"
