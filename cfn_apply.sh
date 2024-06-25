#!/bin/bash
# Simple BASH script to apply CloudFormation or SAM templates.
# Can read a parameter or tag file that contains key=value lines

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Author: Rizvi Rahim
# version 1.39

set -e
export AWS_PAGER=""
export SAM_CLI_TELEMETRY=0

function usage() {
  script="$(basename $0)"
  echo "Usage: 
To automatically use the filename as the stack name (stack-file in this example):

  $script stack-file.yml [stack.parameters] [stack.tags]

To explicitly define the stack name, add an argument to the start:

  $script StackName stack-file.yml [stack.parameters] [stack.tags]

The parameter/tag file, if specified, should be a file with key=value pairs separated by
newlines, with # used for comments.

Optional parametrers:
  $script --no-confirm ...  # Skip confirmation
  $script --sam-build [--use-container] # Run a SAM build before a deployment

Additional commands:
  $script ls  # List stacks
  $script delete <stack-name>  # Delete stack
"
  exit 1
}

if [[ $# == 0 ]]; then
  usage
fi

# Display stack failure error:
function show_stack_error_message() {
  local stack_name=$1
  local apply_timestamp=$2
  aws cloudformation describe-stack-events --stack-name $stack_name --query "StackEvents[?Timestamp >= '"$apply_timestamp"'].ResourceStatusReason" | grep -v "Initiated\|The follow\|Resource creation cancelled" | tail -r | tail -n5
}


# Check if the file has CRLF line endings (which causes issues with tags/parameter files)
function check_crlf() {
  local file_name=$1
  if file "$file_name" | grep -q CRLF; then
    echo "Error: the file $file_name has CRLF (Windows style) line endings. Convert it to LF (unix style) before proceeding"
    exit 4
  fi
}

# Get stack status:
function get_cfn_status() {
  local stack_name=$1
  aws --output text cloudformation describe-stacks --stack-name $stack_name --query Stacks[].StackStatus 2>/dev/null
}

# Wait until the given status:


# Delete stack:
function delete_stack() {
  local stack_name=$1

  # Delete the stack:
  if [[ "$sam_installed" == "yes" ]]; then
    # SAM has enough feedback, no need to do more:
    sam delete --stack-name $stack_name
  else
    # Use AWS CLI, but give feedback on the deletion progress:
    aws cloudformation delete-stack --stack-name $stack_name
    # Status check will return failure once stack is deleted:
    set +e
    # Check status
    while true; do
      current_status=$(get_cfn_status $stack_name)
      if [[ "$current_status" =~ .*FAILED.* ]]; then
        echo "Failed to delete stack, status is $current_status"
        show_stack_error_message $stack_name
        exit 1
      elif [[ "$current_status" == "" ]]; then
        echo "Stack $stack_name successfully deleted"
        exit 0
      else
        echo "$(date) Status for stack $stack_name is $current_status"
      fi
      sleep 3
    done  
    set -e
  fi
}


# Get CFN bucket name, or create CFN bucket if it doesn't exist
function get_cfn_bucket() {

  # Try to reuse the cf-template-<something>-<region> bucket if it exist:
  local region=$(aws ec2 describe-availability-zones --output text --query 'AvailabilityZones[0].[RegionName]')
  # We may not have EC2 permissions:
  if [[ -n "$region" ]]; then
    local bucket_name=$(aws s3api --output text list-buckets --query "Buckets[?starts_with(Name,'cf-templates-') && ends_with(Name, '"$region"')].Name | [0]")
    if [[ -n "$bucket_name"  &&  "$bucket_name" != "None" ]]; then
      echo $bucket_name
      return
    fi
  fi

  # Otherwise check if the cfn-apply script was used to create the bucket before (i.e. bucket starts with cfn-apply):
  local bucket_name=$(aws --output text s3api list-buckets --query "Buckets[?starts_with(Name,'cfn-apply-')].Name")
  if [ -n "$bucket_name" ]; then
    echo $bucket_name
    return
  fi 

  # Bucket doesn't exist, so create a bucket:
  local account_id=$(aws --output text sts get-caller-identity --query Account)
  local bucket_name="cfn-apply-$account_id"
  aws s3 mb s3://$bucket_name > /dev/null
  # Default encryption:
  aws s3api put-bucket-encryption \
    --bucket $bucket_name \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
  # Enable versioning:
  aws s3api put-bucket-versioning \
    --bucket $bucket_name \
    --versioning-configuration Status=Enabled
  # Enable public access block:
  aws s3api put-public-access-block \
    --bucket $bucket_name \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"    

  echo "$bucket_name"
}


ask_confirmation="yes"
# Check for --noconfirm
if [[ "$1" == "--no-confirm" || "$1" == "--noconfirm" ]]; then
  ask_confirmation="no"
  shift
fi

# Check if SAM in installed, if it is, prefer it over awscli as it gives more feedback
use_sam="yes"
if ! command -v sam &> /dev/null; then
 use_sam="no"
fi

sam_build="no"
use_container="no"
# Check for --sambuild & --use-container
if [[ "$1" == "--sam-build" ]]; then
  sam_build="yes"
  shift
fi
if [[ "$1" == "--use-container" ]]; then
  use_container="yes"
  shift
fi


if [ -n "$AWS_PROFILE" ]; then
  echo "Using AWS profile: $AWS_PROFILE"
else
  echo "No AWS_PROFILE environment variable set, using default AWS profile."
fi


# Check for "ls"
if [[ "$1" == "ls" ]]; then
  aws --output table cloudformation describe-stacks --query "Stacks[].{Name: StackName, Status: StackStatus} | sort_by(@, &Name)"
  exit $?
fi

# Check for "delete"
if [[ "$1" == "delete" ]]; then
  shift
  stack_name="$1"
  if [[ "$ask_confirmation" == "yes" ]]; then
    echo "Press enter to delete stack $stack_name, or control+C to cancel"
    read x
  fi
  delete_stack "$stack_name"

fi

# Check if the first parameter has a period, if it does not, it's the stack name
if [[ ! "$1" == *.* ]]; then
  stack_name="$1"
  shift
fi

stack_file=$1
parameter_file=$2
tag_file=$3

if [[ -z "$stack_file" ]]; then
  usage
fi

# Check if template file exists:
if [ ! -f "$stack_file" ]; then
  echo "Error: The stack template file \"$stack_file\" does not exist."
  exit 1
fi

# Check the type of template file
if egrep -q "^Transform:.*AWS::Serverles" $stack_file; then
  template_type="SAM"
  if ! command -v sam &> /dev/null; then
    echo "Error: This seems to be a SAM template, but SAM is not installed."
    exit 1
  fi
else
  template_type="CloudFormation"
fi

# Get the dir, if any. /some/path/My-Stack.yaml -> /some/path/
dir="$(dirname $stack_file)"
filename="$(basename $stack_file)"

# If stack name was not specified, use filename and parameter:
if [ -z "$stack_name" ]; then
  # Use the template file name as the stack name, /some/path/My-Stack.yaml -> My-Stack
  stack_name="${filename%%.*}"
  # If there is a parameter file, append the parameter file name:
  if [ -n "$parameter_file" ]; then
    parameter_filename=$(basename $parameter_file)
    parameter_name="${parameter_filename%%.*}"
    if [[ "$parameter_name" != "$stack_name" ]]; then
      stack_name="${stack_name}-${parameter_name}"
    fi
  fi
  # Convert any underscores to dashes as CFN does like underscores
  stack_name="${stack_name//_/-}"
fi

# Check if stack_name is valid:
stack_pattern="[a-zA-Z][-a-zA-Z0-9]*"
if [[ ! "$stack_name" =~ ^[a-zA-Z][-a-zA-Z0-9]*$ ]]; then
  echo "Stack name \"$stack_name\" is invalid."
  echo "A stack name can contain only alphanumeric characters (case-sensitive) and hyphens. It must start with an alphabetic character."
  exit 1
fi


# Check if a parameter file exists, if specified:
if [ -n "$parameter_file" ] && [ ! -f "$parameter_file" ]; then
  echo "Error: Parameter file \"$parameter_file\" does not exist"
  exit 2
fi

# Check if a tag file exists, if specified:
if [ -n "$tag_file" ] && [ ! -f "$tag_file" ]; then
  echo "Error: Tag file \"$tag_file\" does not exist"
  exit 2
fi

# Prepare arguments to cloudformation_deploy
# Using BASH arrays as parameter or tag values may have spaces
cfn_deploy_args=( --no-fail-on-empty-changeset --capabilities CAPABILITY_NAMED_IAM )


function file_to_arguments() {
  # Function to convert a given file to arguments
  local file="$1"
  # The || [ -n $line ] is a workaround for visual studio code
  # which writes files without the trailing newline
  while IFS= read -r line || [ -n "$line" ]; do
    # Skip lines starting with '#':
    if [[ $line =~ ^\# ]]; then
      continue
    fi
    # Skip lines that don't have an =
    if [[ "$line" != *"="* ]]; then
      continue
    fi
    # Remove text after a '#', eg. "aparam=x # comment"
    line="${line%#*}"
    # Remove quotes
    line="${line//\"/}"
    line="${line//\'/}"

    if [[ "$use_sam" == "no" ]]; then 
      cfn_deploy_args+=( "$line" )
    fi

    if [[ "$use_sam" == "yes" ]]; then 
      # Specifying key=value in parameter-overrides causes issues with spaces with SAM
      # So separating the ParameterKey and ParameterValue:
      # Get key/value:
      local key="${line%=*}"
      local value="${line##*=}"
      # Add argument:
      cfn_deploy_args+=( "ParameterKey=$key,ParameterValue='$value'" )
    fi
  done < "$file"
}

if [ -s "$parameter_file" ]; then
  check_crlf "$parameter_file"
  cfn_deploy_args+=("--parameter-overrides")
  file_to_arguments "$parameter_file"
fi

# Check if a tags file exists:
if [ -f "$tag_file" ]; then
  check_crlf "$tag_file"
  cfn_deploy_args+=("--tags")
  file_to_arguments "$tag_file"
fi


# Check if template file is is more than 51,200 bytes:
# For mac+linux compatibility, we can't use stat, or du -b (doesn't work on mac), 
# so use du -k (number of 1024 byte blocks)
template_bytes=$(du -Lk "$stack_file" | cut -f1)
if [[ "$template_bytes" -ge 50 || "$template_type" == "SAM" ]]; then
  # Create a bucket if required:
  bucket=$(get_cfn_bucket)
  s3_prefix=cfn_apply
  echo "Using S3 bucket $bucket as temporary storage"  
  # Update the arguments:
  cfn_deploy_args+=(--s3-bucket $bucket --s3-prefix $s3_prefix --force-upload)
fi

# Check if the stack already exist
stack_exists="yes"
aws cloudformation describe-stacks --stack-name $stack_name > /dev/null 2>&1 || stack_exists="no"

# Disable checking for failures to be able to detect failed stack creation:
set +e

# Display parameters before running the apply:
if [[ "$stack_exists" == "yes" ]]; then
  action="UPDATE"
else
  action="CREATE"
fi
echo "Running $action on $template_type stack name $stack_name"
if [ -f "$parameter_file" ]; then
  echo "Using the parameter file $parameter_file:"
  echo "------"
  cat "$parameter_file"
  echo ''
  echo "------"
fi


# Store the current timestamp, so that we can search for events
# after the given timestamp:
apply_timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.000000+00:00)

# Set stack name:
cfn_deploy_args+=(--stack-name $stack_name)

# If SAM is not installed, just use the AWS CLI:
if [[ "$use_sam" == "no" ]]; then

  if [[ "$ask_confirmation" == "yes" ]]; then
    echo 'Press control+C to cancel, or enter to continue.'
    read x
  fi
  aws cloudformation deploy --template-file "$stack_file"  "${cfn_deploy_args[@]}"
  cfn_return=$?

# SAM:
else
  if [[ "$ask_confirmation" == "yes" ]]; then
    cfn_deploy_args+=(--confirm-changeset)
  fi

  # The --template-file is not required if using sam build:
  if [[ "$sam_build" == "no" ]]; then
    cfn_deploy_args+=(--template-file "$stack_file")
  else
    # sam_build == yes
    if [[ "$use_container" == "yes" ]]; then
      sam build --use-container --template-file "$stack_file" 
    else
      sam build --template-file "$stack_file" 
    fi
  fi
  sam deploy --stack-name $stack_name "${cfn_deploy_args[@]}"
  cfn_return=$?
fi


if [ $cfn_return != 0 ]; then
  echo "Got error code $cfn_return"
  echo "Failed to apply stack"
  # Try to display the error message
  show_stack_error_message $stack_name $apply_timestamp

  if [[ "$stack_exists" == "no" ]]; then
    echo "Press enter to delete the failed stack"
    read x
    aws cloudformation delete-stack --stack-name $stack_name
    echo "Sent delete request for stack $stack_name"
  fi
  exit 1
else
  # Display outputs if any
  echo "All OK!"
  aws cloudformation describe-stacks --stack-name $stack_name --query "Stacks[].Outputs[].{Key: OutputKey, Value: OutputValue} | sort_by(@, &Key)"  --output table --no-paginate
fi

