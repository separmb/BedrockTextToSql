from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_apigatewayv2 as apigwv2,
    aws_bedrock as bedrock,
    RemovalPolicy,
    Duration,
    Size,
)
from aws_cdk.aws_apigatewayv2_integrations import WebSocketLambdaIntegration
from constructs import Construct

from cdk_nag import ( AwsSolutionsChecks, NagSuppressions )

class ConverseText2SqlAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self, "MyVpc",
            max_azs=2,  # Number of Availability Zones
            cidr="10.0.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ],
            nat_gateways=1  # NAT Gateway for private subnets
        )

        # set up bastion host
        # Security group allowing SSH and HTTP
        bastion_host_sg = ec2.SecurityGroup(
            self, "BastionHostSG",
            vpc=vpc,
            description="Allow SSH and HTTP",
            allow_all_outbound=True
        )
 
        # allow access to bastion from Amazon workspaces
        bastion_host_sg.add_ingress_rule(ec2.Peer.ipv4('3.83.200.219/32'), ec2.Port.tcp(22), "Allow SSH")

        # Amazon Linux 2 AMI
        ami = ec2.MachineImage.latest_amazon_linux2()

        # create user data for EC2
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "yum update -y",
            "sudo yum -y install mysql"
        )


        # Create EC2 instance in the public subnet
        instance = ec2.Instance(
            self, "MyInstance",
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ami,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=bastion_host_sg,
            key_name="separ-key-pair",  # Replace with your EC2 key pair name
            associate_public_ip_address=True,
            user_data=user_data
        )

        # get private subnets from our VPC
        private_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets

        # Create DynamoDB table
        dynamodb_table = dynamodb.Table(
            self, "TEXT2SQLTable",
            table_name="advtext2sql_memory_tb",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create RDS MySQL instance
        db_secret = secretsmanager.Secret(
            self, "DBSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key="password",
                exclude_punctuation=True,
                include_space=False
            )
        )

        db_subnet_group = rds.SubnetGroup(
            self, "DBSubnetGroup",
            vpc=vpc,
            description="Subnet group for RDS database",
            vpc_subnets=ec2.SubnetSelection(subnets=private_subnets)
        )
        
        # Create a security group for RDS and Lambda. For POC purpose we are using a same Security group for both RDS and Lambda but when implementing as per best practice it is good to use seperate security groups.
        security_group = ec2.SecurityGroup(
            self, "SharedSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for RDS and Lambda"
        )
        
        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic(),
            description="Allow all inbound traffic from VPC CIDR"
        )
         
        security_group.add_ingress_rule(
            peer=bastion_host_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow all inbound traffic on port 3306 from bastion"
        )
        
        db_instance = rds.DatabaseInstance(
            self, "MyRDSInstance",
            instance_identifier="myrdsdatabase",
            engine=rds.DatabaseInstanceEngine.MYSQL,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=private_subnets),
            subnet_group=db_subnet_group,
            credentials=rds.Credentials.from_secret(db_secret),
            multi_az=False,
            allocated_storage=20,
            max_allocated_storage=100,
            security_groups=[security_group],
            publicly_accessible=False,
            delete_automated_backups=True,
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY 
        )

        # Create VPC Endpoints
        dynamodb_endpoint = vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            subnets=[ec2.SubnetSelection(subnets=private_subnets)]
        )
        secrets_manager_endpoint = vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(subnets=private_subnets),
            security_groups=[security_group]
        )
        bedrock_endpoint = vpc.add_interface_endpoint(
            "BedrockEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
            subnets=ec2.SubnetSelection(subnets=private_subnets),
            security_groups=[security_group]
        )

        # Create Lambda function
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        # Add permissions for DynamoDB, Secrets Manager, and Bedrock
        
        # Grant DynamoDB permissions
        dynamodb_table.grant_read_write_data(lambda_role)

        # Grant Secrets Manager permissions
        db_secret.grant_read(lambda_role)
        
        
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"))
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:ApplyGuardrail"],
            resources=[f"*"]
        ))

        # Create Lambda layers
        layer1 = lambda_.LayerVersion(
            self, "psycopg2_final",
            layer_version_name="layer_content",
            code=lambda_.Code.from_asset("./src/layers/layer_content.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11]
        )        

        # Create DynamoDB table to store connections
        connections_table = dynamodb.Table(
            self, "ConnectionsTable",
            table_name="websocket-connections",
            partition_key=dynamodb.Attribute(
                name="connectionId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create Lambda function
        lambda_function = lambda_.Function(
            self, "SQLAgentFunction",
            function_name="sqlagent",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset("./src/ConverseSqlAgent"),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=private_subnets),
            security_groups=[security_group],
            layers=[layer1],
            role=lambda_role,
            memory_size=1024,
            ephemeral_storage_size=Size.gibibytes(2),
            timeout=Duration.minutes(15),
            environment={
                "DynamoDbMemoryTable": dynamodb_table.table_name,
                "BedrockModelId": "us.anthropic.claude-sonnet-4-20250514-v1:0",
                "CONNECTIONS_TABLE": connections_table.table_name,
                "BEDROCK_GUARDRAIL_ID": "l2m1ls0o9cth",
                "BEDROCK_GUARDRAIL_VERSION": "20"
            }
        )

        # Grant permissions
        dynamodb_table.grant_read_write_data(lambda_function)
        db_secret.grant_read(lambda_function)

        # Lambda function for $connect route
        connect_handler = lambda_.Function(
            self, "ConnectHandler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="connect.handler",
            code=lambda_.Code.from_asset("./src/ConverseSqlAgent"),
            environment={
                "CONNECTIONS_TABLE": connections_table.table_name
            }
        )

        # Lambda function for $disconnect route
        disconnect_handler = lambda_.Function(
            self, "DisconnectHandler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="disconnect.handler",
            code=lambda_.Code.from_asset("./src/ConverseSqlAgent"),
            environment={
                "CONNECTIONS_TABLE": connections_table.table_name
            }
        )

        # Grant DynamoDB permissions to Lambda functions
        connections_table.grant_read_write_data(connect_handler)
        connections_table.grant_read_write_data(disconnect_handler)
        connections_table.grant_read_write_data(lambda_function)

        # Create public S3 bucket for the angular app and upload file to bucket
        bucket = s3.Bucket(
            self, "Text2SqlAngularBucket",
            bucket_name=f"text2sql-angular-app-{self.account}-{self.region}",  # Ensure unique name
            website_index_document="index.html",
            website_error_document="index.html",  # For Angular routing
            public_read_access=False,
            removal_policy=RemovalPolicy.DESTROY,  # Be careful with this in production
            auto_delete_objects=True  # This will delete objects when stack is destroyed
        )

        # Create a bucket policy statement for public read access
        # policy_statement = iam.PolicyStatement(
        #     effect=iam.Effect.ALLOW,
        #     principals=[iam.AnyPrincipal()],  # Example: allow all (use cautiously)
        #     actions=["s3:GetObject"],
        #     resources=[f"{bucket.bucket_arn}/*"]
        # )

        # Attach the policy to the bucket
        # bucket.add_to_resource_policy(policy_statement)

        # Deploy files from local directory to S3
        deployment = s3deploy.BucketDeployment(
            self, "AngularAppDeployment",
            sources=[
                s3deploy.Source.asset("./angular/ng-text-to-sql.zip")  
            ],
            destination_bucket=bucket,
            # Invalidate CloudFront cache if using CloudFront
            # distribution=distribution,
            # distribution_paths=["/*"]
        )

        # Create WebSocket API
        web_socket_api = apigwv2.WebSocketApi(
            self, "MyWebSocketApi",
            api_name="MyWebSocketApi",
            description="WebSocket API for real-time communication",
            connect_route_options=apigwv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration(
                    "ConnectIntegration", 
                    connect_handler
                )
            ),
            disconnect_route_options=apigwv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration(
                    "DisconnectIntegration", 
                    disconnect_handler
                )
            ),
            default_route_options=apigwv2.WebSocketRouteOptions(
                integration=WebSocketLambdaIntegration(
                    "DefaultIntegration", 
                    lambda_function
                )
            )
        )

        # Create WebSocket Stage
        stage = apigwv2.WebSocketStage(
            self, "MyWebSocketStage",
            web_socket_api=web_socket_api,
            stage_name="dev",
            description="Development stage",
            auto_deploy=True
        )

        # Grant API Gateway Management API permissions to Lambda functions
        # This allows Lambda to send messages back to connected clients
        api_gateway_management_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["execute-api:ManageConnections"],
            resources=[f"arn:aws:execute-api:{self.region}:{self.account}:{web_socket_api.api_id}/*"]
        )
        
        lambda_function.add_to_role_policy(api_gateway_management_policy)


