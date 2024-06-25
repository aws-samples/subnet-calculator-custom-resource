## Subnet Calculator AWS CloudFormation custom resource

While [Fn::Cidr](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-cidr.html) can be used in [AWS CloudFormation](https://aws.amazon.com/cloudformation/) to split a given CIDR evenly, if you need to create an [Amazon Virtual Private Cloud (VPC)](https://aws.amazon.com/vpc/) with subnets of different sizes (eg. smaller public subnet with a large private subnet, or a /28 [AWS Transit Gateway](https://aws.amazon.com/transit-gateway/) [attachment subnet](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html)), or a parameterized number of subnets/AZs, this custom resource should be useful. This is an [Amazon SNS backed](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-sns.html) CloudFormation custom resource accessible by all accounts in the [AWS Organization](https://aws.amazon.com/organizations/), that can take a given VPC CIDR string, and split it to different sized subnets.

It can be used like this in a VPC template:

```yaml
  SubnetCalculator:
    Type: Custom::SubnetCalculator
    Properties:
      ServiceToken: !Sub arn:aws:sns:${AWS::Region}:${NetworkAccountID}:SubnetCalculatorV1
      VPCNetwork: 10.113.0.0/23
      AZs: 3
      Subnets:
        - Label: Private1
          Prefix: 26
        - Label: Private2
          Prefix: 27
        - Label: Public
          Prefix: 27
        - Label: TGW
          Prefix: 28
```

A "Prefix" of 0 means that subnet is skipped as though it wasn't listed.

The resource returns attributes for each subnet Label given, with an array of the CIDRs:

```yaml
Private1:
  - 10.113.0.0/27
  - 10.113.0.32/27
  - 10.113.0.64/27
Private2:
  - 10.113.0.96/28
  - 10.113.0.112/28
  - 10.113.0.128/28
TGW:
  - 10.113.0.208/28
  - 10.113.0.224/28
  - 10.113.0.240/28
```

To get the first Private1 subnet in the VPC template, you can use `!Select [ 0, !GetAtt SubnetCalculator.Private1 ]`, and the second Private1 subnet `!Select [ 1, !GetAtt SubnetCalculator.Private1 ]`, and so on.


## Installation/update

This is meant to run in an AWS Organizations environment. Select an account that this should run on, for example the Network account or Shared Services account. Make sure you have the SAM CLI installed, or just use [AWS CloudShell](https://aws.amazon.com/cloudshell/).

The template creates an SNS topic with a resource policy allowing accounts in the same AWS Organization to Publish messages, which in turn triggers a Lambda function containing the calculator. A [CloudFormation custom resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-sns.html) can be then included in your VPC templates to call that SNS topic from any account.

To install or update the template, run: 

```
./install.sh
```

It will output the SNS topic ARN that should be referenced by the VPC templates.


## Custom resource testing

To make sure that the custom resource is working, you can create the CloudFormation template [tests/test_basic_cfn_resource.yaml](tests/test_basic_cfn_resource.yaml) in any AWS account. Go to the Outputs tab to see if the calculator was able to divide up the sample VPC CIDR.

For an advanced example of a complex customizable VPC template (which can potentially be deployed via AWS Service Catalog) that uses this subnet calculator, see [tests/example_sample_advanced_vpc.yaml](tests/example_sample_advanced_vpc.yaml), which depends on the [Network Orchestration for AWS Transit Gateway](https://aws.amazon.com/solutions/implementations/network-orchestration-aws-transit-gateway/) running to connect to Transit Gateway and configure the Transit Gateway route tables automatically.


## Local testing (developers)

To test the function locally, just run `python3 src/subnet_calculator_v1.py`, and edit the `__main__` section as required.

For a more thorough check, there is a list of sample VPC CIDRs, subnet prefixes and expected responses in the `tests/test_cidrs.py` file. The `calculateSubnetCIDR()` function is run for each of them. When making changes to the algorithm, run the tests with:

```bash
cd src
python3 -m pytest ../tests/
```

If you ever develop the calculateSubnetCIDR() function that results in a breaking change (i.e. the existing tests do not pass), consider creating a separate V2 version of this SNS/Lambda template, so that older VPCs using the V1 method do not have the CIDRs changed.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

