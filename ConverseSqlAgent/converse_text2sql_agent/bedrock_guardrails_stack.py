from aws_cdk import (
    Stack,
    aws_bedrock as bedrock,
    custom_resources as cr,
)
from constructs import Construct
from typing import List, Dict, Any


class TextToSqlGuardrailStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create the main guardrail for text-to-SQL agent
        self.text_to_sql_guardrail = self._create_text_to_sql_guardrail()
        
        # Create a version of the guardrail
        self.guardrail_version = self._create_guardrail_version()

        
    def _create_text_to_sql_guardrail(self) -> bedrock.CfnGuardrail:
        """Create the main guardrail with all necessary filters for text-to-SQL"""
        
        return bedrock.CfnGuardrail(
            self, "TextToSqlGuardrail",
            name="text-to-sql-guardrail",
            description="Basic guardrail checking for blocked sql key works",
            
            # Blocked messages
            blocked_input_messaging="I cannot process this request as it may contain inappropriate content or unsafe SQL operations.",
            blocked_outputs_messaging="I cannot generate this SQL query as it may contain unsafe operations or inappropriate content.",
            
            # Content Policy Configuration - Enhanced security for SQL context
            # content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
            #     filters_config=[
            #         # Block prompt attacks (jailbreaks, prompt injection)
            #         bedrock.CfnGuardrail.ContentFilterConfigProperty(
            #             type="PROMPT_ATTACK",
            #             input_strength="HIGH",
            #             output_strength="NONE"
            #         ),
            #         # Medium filtering for other harmful content
            #         bedrock.CfnGuardrail.ContentFilterConfigProperty(
            #             type="HATE",
            #             input_strength="MEDIUM",
            #             output_strength="MEDIUM"
            #         ),
            #         bedrock.CfnGuardrail.ContentFilterConfigProperty(
            #             type="INSULTS",
            #             input_strength="MEDIUM",
            #             output_strength="MEDIUM"
            #         ),
            #         bedrock.CfnGuardrail.ContentFilterConfigProperty(
            #             type="SEXUAL",
            #             input_strength="MEDIUM",
            #             output_strength="MEDIUM"
            #         ),
            #         bedrock.CfnGuardrail.ContentFilterConfigProperty(
            #             type="VIOLENCE",
            #             input_strength="MEDIUM",
            #             output_strength="MEDIUM"
            #         )
            #     ],
            # ),
            
            # Topic Policy Configuration - SQL-specific denied topics
            # topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(
            #     topics_config=self._get_denied_topics_config(),
            # ),
            
            # Word Policy Configuration - Block dangerous SQL keywords
            word_policy_config=bedrock.CfnGuardrail.WordPolicyConfigProperty(
                words_config=self._get_word_filters_config(),
                managed_word_lists_config=[
                    bedrock.CfnGuardrail.ManagedWordsConfigProperty(
                        type="PROFANITY"
                    )
                ]
            ),
            
            # Sensitive Information Policy - Protect PII and credentials
            # sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
            #     pii_entities_config=self._get_pii_entities_config(),
            #     regexes_config=self._get_regex_filters_config()
            # ),
            
            # Contextual Grounding Policy - Prevent SQL hallucinations
            # contextual_grounding_policy_config=bedrock.CfnGuardrail.ContextualGroundingPolicyConfigProperty(
            #     filters_config=[
            #         bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
            #             type="GROUNDING",
            #             threshold=0.8  # High threshold for SQL accuracy
            #         ),
            #         bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
            #             type="RELEVANCE",
            #             threshold=0.8  # Ensure SQL is relevant to query
            #         )
            #     ]
            # ),
        )

    def _get_denied_topics_config(self) -> List[bedrock.CfnGuardrail.TopicConfigProperty]:
        """Configure denied topics specific to SQL security"""
        return [            
            # Bulk Data Operations
            bedrock.CfnGuardrail.TopicConfigProperty(
                name="Bulk Data Operations",
                definition="Queries that perform bulk data operations, mass deletions, or could potentially cause data loss.",
                examples=[
                    "DELETE FROM table WHERE 1=1",
                    "UPDATE table SET column=value",
                    "INSERT INTO table SELECT * FROM",
                    "BULK INSERT operations",
                    "Mass data export"
                ],
                type="DENY"
            ),

            # Write actions
            bedrock.CfnGuardrail.TopicConfigProperty(
                name="SQL Write Operations Block",
                definition="SQL statements that perform write operations including INSERT, UPDATE, DELETE.",
                examples=[
                    "INSERT INTO users VALUES (1, 'John')",
                    "UPDATE users SET name = 'Jane' WHERE id = 1",
                    "DELETE FROM users WHERE id = 1",
                    "DROP TABLE users",
                ],
                type="DENY",
            ),
        ]

    def _get_word_filters_config(self) -> List[bedrock.CfnGuardrail.WordConfigProperty]:
        """Configure word filters for dangerous SQL keywords and operations"""
        
        dangerous_sql_keywords = [
            # DDL Operations
            "DROP TABLE", "DROP DATABASE", "DROP SCHEMA", "DROP VIEW",
            "ALTER TABLE", "ALTER DATABASE", "ALTER SCHEMA",
            "CREATE USER", "DROP USER", "ALTER USER",
            
            # DML Operations
            "DELETE FROM", "TRUNCATE TABLE", "TRUNCATE",
            "UPDATE SET", "INSERT INTO SELECT",
            
            # DCL Operations
            "GRANT ALL", "GRANT PRIVILEGES", "REVOKE",
            "GRANT SELECT", "GRANT INSERT", "GRANT UPDATE", "GRANT DELETE",
            
            # System Functions and Procedures
            "xp_cmdshell", "sp_configure", 
            "OPENROWSET", "OPENDATASOURCE", "BULK INSERT",
            
            # Database-specific dangerous functions
            "LOAD_FILE", "INTO OUTFILE", "INTO DUMPFILE",
            "UNION SELECT", "UNION ALL SELECT",
            
            # Administrative commands
            "SHUTDOWN", "RESTART", "KILL", "SHOW PROCESSLIST",
            "FLUSH PRIVILEGES", "RESET MASTER", "RESET SLAVE"
        ]
        
        return [
            bedrock.CfnGuardrail.WordConfigProperty(text=keyword)
            for keyword in dangerous_sql_keywords
        ]

    def _get_pii_entities_config(self) -> List[bedrock.CfnGuardrail.PiiEntityConfigProperty]:
        """Configure PII entity detection for SQL context"""
        
        pii_entities = [
            "ADDRESS", "AGE", "AWS_ACCESS_KEY",
            "CA_HEALTH_NUMBER", "CA_SOCIAL_INSURANCE_NUMBER",
            "CREDIT_DEBIT_CARD_CVV", "CREDIT_DEBIT_CARD_EXPIRY",
            "CREDIT_DEBIT_CARD_NUMBER", "DRIVER_ID", "EMAIL", "INTERNATIONAL_BANK_ACCOUNT_NUMBER",
            "IP_ADDRESS", "LICENSE_PLATE", "MAC_ADDRESS",
            "NAME", "PASSWORD", "PHONE", "PIN",
            "SWIFT_CODE", "UK_NATIONAL_HEALTH_SERVICE_NUMBER",
            "UK_NATIONAL_INSURANCE_NUMBER", "UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER",
            "URL", "USERNAME", "US_BANK_ACCOUNT_NUMBER",
            "US_BANK_ROUTING_NUMBER", "US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER",
            "US_PASSPORT_NUMBER", "US_SOCIAL_SECURITY_NUMBER",
            "VEHICLE_IDENTIFICATION_NUMBER"
        ]
        
        return [
            bedrock.CfnGuardrail.PiiEntityConfigProperty(
                type=entity,
                action="BLOCK"  # Block rather than anonymize for SQL context
            )
            for entity in pii_entities
        ]

    # def _get_regex_filters_config(self) -> List[bedrock.CfnGuardrail.RegexConfigProperty]:
    #     """Configure regex filters for SQL-specific patterns"""
        
    #     return [
            
    #         # SQL injection patterns
    #         bedrock.CfnGuardrail.RegexConfigProperty(
    #             name="SQL Injection Patterns",
    #             description="Common SQL injection attack patterns",
    #             pattern=r"(\bOR\b\s+\d+\s*=\s*\d+|\bUNION\b\s+\bSELECT\b|;\s*--|\bDROP\b\s+\bTABLE\b)",
    #             action="BLOCK"
    #         ),
            
    #         # API Keys and Tokens
    #         bedrock.CfnGuardrail.RegexConfigProperty(
    #             name="API Keys",
    #             description="Detect API keys and access tokens",
    #             pattern=r"(api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?",
    #             action="BLOCK"
    #         ),
            
    #         # Password patterns
    #         bedrock.CfnGuardrail.RegexConfigProperty(
    #             name="Password Patterns",
    #             description="Detect password assignments or references",
    #             pattern=r"(password|pwd|pass)\s*[:=]\s*['\"][^'\"]+['\"]",
    #             action="ANONYMIZE"
    #         ),
            
    #         # Credit card numbers
    #         bedrock.CfnGuardrail.RegexConfigProperty(
    #             name="Credit Card Numbers",
    #             description="Detect credit card number patterns",
    #             pattern=r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    #             action="BLOCK"
    #         )
    #     ]

    def _create_guardrail_version(self) -> bedrock.CfnGuardrailVersion:
        return bedrock.CfnGuardrailVersion(
            self, "TextToSqlGuardrailVersion",
            guardrail_identifier=self.text_to_sql_guardrail.attr_guardrail_id,
            description="Production version of text-to-SQL guardrail"
        )




