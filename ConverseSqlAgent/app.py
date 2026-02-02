#!/usr/bin/env python3
import os

import aws_cdk as cdk

from converse_text2sql_agent.converse_text2sql_agent_stack import ConverseText2SqlAgentStack
from converse_text2sql_agent.bedrock_guardrails_stack import TextToSqlGuardrailStack


app = cdk.App()

# set up bedrock guardrails first
bedrockGuardRails = TextToSqlGuardrailStack(
    app, 
    "TextToSqlGuardrailStack",
    description="Amazon Bedrock Guardrails for Text-to-SQL Agent",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

# then set up rest of stack
main_stack = ConverseText2SqlAgentStack(app, "ConverseText2SqlAgentStack", guardrail=bedrockGuardRails.text_to_sql_guardrail, 
    guardrailVersion=bedrockGuardRails.guardrail_version,
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

main_stack.add_dependency(bedrockGuardRails)

app.synth()
