#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_software_pipeline.cdk_stack import CdkSofrwarePipelineStack

app = cdk.App()
CdkSofrwarePipelineStack(app, "CdkSoftwarePipelineStack")
app.synth()
