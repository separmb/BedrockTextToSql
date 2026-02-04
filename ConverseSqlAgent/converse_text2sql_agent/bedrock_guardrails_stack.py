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
            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    # Block prompt attacks (jailbreaks, prompt injection)
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="PROMPT_ATTACK",
                        input_strength="NONE",
                        output_strength="NONE"
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="HATE",
                        input_strength="MEDIUM",
                        output_strength="MEDIUM"
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="INSULTS",
                        input_strength="LOW",
                        output_strength="LOW"
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="SEXUAL",
                        input_strength="MEDIUM",
                        output_strength="MEDIUM"
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="VIOLENCE",
                        input_strength="MEDIUM",
                        output_strength="MEDIUM"
                    )
                ],
            ),
            
            # Topic Policy Configuration - SQL-specific denied topics
            topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=self._get_denied_topics_config(),
            ),
            
            # Word Policy Configuration - Block dangerous SQL keywords
            word_policy_config=bedrock.CfnGuardrail.WordPolicyConfigProperty(
                words_config=self._get_word_filters_config(),
                managed_word_lists_config=[
                    bedrock.CfnGuardrail.ManagedWordsConfigProperty(
                        type="PROFANITY"
                    )
                ]
            ),

            # Sensitive Information Policy - Protect against SQL injection
            sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
                regexes_config=self._get_regex_filters_config()
            ),
            
            # Contextual Grounding Policy - Prevent SQL hallucinations
            contextual_grounding_policy_config=bedrock.CfnGuardrail.ContextualGroundingPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
                        type="GROUNDING",
                        threshold=0.8  # High threshold for SQL accuracy
                    ),
                    bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
                        type="RELEVANCE",
                        threshold=0.8  # Ensure SQL is relevant to query
                    )
                ]
            ),
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

             # sql injections
            bedrock.CfnGuardrail.TopicConfigProperty(
                name="SQL Injection Attacks",
                definition="Prevent SQL injection attempts and malicious database queries.",
                examples=[
                    "'; DROP TABLE users; --",
                    "1' OR '1'='1",
                    "UNION SELECT * FROM passwords",
                    "'; INSERT INTO admin VALUES ('hacker', 'password'); --",
                    "1' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 --"
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

    def _get_regex_filters_config(self) -> List[bedrock.CfnGuardrail.RegexConfigProperty]:       
        return [
            # SQL injection patterns
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="SQL Injection Patterns",
                description="Common SQL injection attack patterns",
                pattern="(?i)(\\bUNION\\b.*\\bSELECT\\b|\\bOR\\b.*\\b1\\s*=\\s*1\\b|\\bAND\\b.*\\b1\\s*=\\s*1\\b|';.*--|\\bDROP\\b.*\\bTABLE\\b|\\bINSERT\\b.*\\bINTO\\b.*\\bVALUES\\b|\\bUPDATE\\b.*\\bSET\\b|\\bDELETE\\b.*\\bFROM\\b)",
                action="BLOCK"
            ),
        ]
    def _create_guardrail_version(self) -> bedrock.CfnGuardrailVersion:
        return bedrock.CfnGuardrailVersion(
            self, "TextToSqlGuardrailVersion",
            guardrail_identifier=self.text_to_sql_guardrail.attr_guardrail_id,
            description="Production version of text-to-SQL guardrail"
        )




