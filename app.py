#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_software_pipeline.cdk_stack import CdkSoftwarePipelineStack

app = cdk.App()
CdkSoftwarePipelineStack(app, "CdkSoftwarePipelineStack")
app.synth()
