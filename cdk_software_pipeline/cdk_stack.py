from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cp_actions,
    aws_elasticloadbalancingv2 as elbv2,
    aws_codebuild as codebuild,
    core,
    SecretValue
)
from constructs import Construct
import os

class CdkSofrwarePipelineStack(Stack):

    @property
    def vpc(self):
        return self.cdk_lab_vpc
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        # Define the VPC
        vpc = ec2.Vpc(
            self, "cdk_vpc",
            cidr="10.0.0.0/18",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet1",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )],
            nat_gateways=0
            )
        
        # ELB Security Group
        elb_sg = ec2.SecurityGroup(
            self, "ElbSecurityGroup",
            vpc=vpc,
            description="Allow http access from everywhere",
            allow_all_outbound=True
            )
        
        elb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))

        webserver_sg = ec2.SecurityGroup(
            self, "WebserverSecurityGroup",
            vpc=vpc,
            description="Allow SSH and HTTP"
            )
        
        webserver_sg.add_ingress_rule(ec2.Peer.ipv4(f'{os.environ["MY_IP"]}/32'), ec2.Port.tcp(22))
        webserver_sg.add_ingress_rule(elb_sg, ec2.Port.tcp(80), "Allow from ELB")

        web_instance_role = iam.Role(
            self, "WebInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess")]
            )

        codebuild_project = codebuild.PipelineProject(
            self, "CodeBuildProject",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0),
                environment_variables={
                    "SOME_VAR": codebuild.BuildEnvironmentVariable(value="SomeValue")})

        artifact_bucket = s3.Bucket(
            self, "ArtifactBucket",
            encryption=s3.BucketEncryption.S3_MANAGED
            )
        
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            artifact_bucket=artifact_bucket,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[cp_actions.GitHubSourceAction(
                        action_name="GitHub_Source",
                        owner=os.environ["GITHUB_USERNAME"],
                        repo=os.environ["REPO_NAME"],
                        oauth_token=SecretValue.plain_text(os.environ["YOUR_OAUTH_TOKEN"]),
                        output=source_output,
                        trigger=cp_actions.GitHubTrigger.NONE
                        )]),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[cp_actions.CodeBuildAction(
                        action_name="CodeBuild",
                        project=codebuild_project,
                        input=source_output,
                        outputs=[build_output])]
                    )
                ]
            )