"""
Configuration summary logging utilities for the inference server.

This module handles logging comprehensive configuration summaries, including:
- Server mode and provider configurations
- Service settings and capabilities
- API settings and security configurations
- Model information and endpoint details
- System monitoring and debugging information
"""

import logging
from typing import Dict, Any, Optional, NoReturn
from fastapi import FastAPI
from config.config_manager import _is_true_value


class ConfigurationSummaryLogger:
    """
    Handles comprehensive configuration summary logging for the inference server.
    
    This class is responsible for:
    - Logging server configuration overviews
    - Providing detailed provider and service information
    - Formatting configuration data for easy reading
    - Supporting debugging and system monitoring
    - Generating documentation-ready configuration reports
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        """
        Initialize the ConfigurationSummaryLogger.
        
        Args:
            config: The application configuration dictionary
            logger: Logger instance for configuration summary logging
        """
        self.config = config
        self.logger = logger
    
    def log_configuration_summary(self, app: Optional[FastAPI] = None) -> None:
        """
        Log a comprehensive summary of the server configuration.
        
        This method provides a detailed overview of the server's configuration
        by logging key settings and their values. It includes:
        - Server mode (Full/Inference-only)
        - Provider configurations
        - Service settings
        - API settings
        - Model information
        - Endpoint information
        
        The summary is formatted for easy reading and includes:
        - Clear section headers
        - Grouped related settings
        - Enabled/disabled status
        - Provider and model details
        
        This summary is logged at server startup to help with:
        - Configuration verification
        - Debugging
        - System monitoring
        - Documentation
        
        Args:
            app: Optional FastAPI application instance for accessing runtime state
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info("Server Configuration Summary")
            self.logger.info("=" * 50)
            
            # Log server mode information
            self._log_server_mode()
            
            # Log provider configurations
            self._log_provider_configurations()
            
            # Log service configurations
            self._log_service_configurations()
            
            # Log API and security configurations
            self._log_api_configurations()
            
            # Log model information
            self._log_model_information()
            
            # Log runtime information if app is available
            if app:
                self._log_runtime_information(app)
            
            # Log endpoint information
            self._log_endpoint_information()
            
            # Log system settings
            self._log_system_settings()
        except Exception as e:
            self.logger.error(f"Error logging configuration summary: {str(e)}")
            # Continue execution - don't let logging errors break the application
    
    def _log_server_mode(self) -> None:
        """Log server mode and operational settings."""
        try:
            inference_only = _is_true_value(self.config.get('general', {}).get('inference_only', False))
            
            # Log mode first and prominently
            self.logger.info(f"Mode: {'INFERENCE-ONLY' if inference_only else 'FULL'} (RAG {'disabled' if inference_only else 'enabled'})")
            self.logger.info("-" * 50)
        except Exception as e:
            self.logger.error(f"Error logging server mode: {str(e)}")
    
    def _log_provider_configurations(self) -> None:
        """Log provider configuration details."""
        try:
            # Get selected providers
            inference_provider = self.config.get('general', {}).get('inference_provider', 'ollama')
            self.logger.info(f"Inference provider: {inference_provider}")
            
            # Only log embedding info if not in inference_only mode
            inference_only = _is_true_value(self.config.get('general', {}).get('inference_only', False))
            if not inference_only:
                # Get embedding configuration
                embedding_config = self.config.get('embedding', {})
                embedding_enabled = _is_true_value(embedding_config.get('enabled', True))
                embedding_provider = embedding_config.get('provider', 'ollama')
                
                self.logger.info(f"Embedding: {'enabled' if embedding_enabled else 'disabled'}")
                if embedding_enabled:
                    self.logger.info(f"Embedding provider: {embedding_provider}")
                    if embedding_provider in self.config.get('embeddings', {}):
                        embed_model = self.config['embeddings'][embedding_provider].get('model', 'unknown')
                        self.logger.info(f"Embedding model: {embed_model}")
        except Exception as e:
            self.logger.error(f"Error logging provider configurations: {str(e)}")
    
    def _log_service_configurations(self) -> None:
        """Log service configuration details."""
        try:
            # Log LLM Guard service information
            llm_guard_config = self.config.get('llm_guard', {})
            
            # Check if enabled field exists or if section exists
            if llm_guard_config:
                if 'enabled' in llm_guard_config:
                    # Structure with explicit enabled field
                    llm_guard_enabled = llm_guard_config.get('enabled', False)
                else:
                    # Simplified structure - if section exists, it's enabled
                    llm_guard_enabled = True
            else:
                llm_guard_enabled = False
            
            self.logger.info(f"LLM Guard: {'enabled' if llm_guard_enabled else 'disabled'}")
            
            if llm_guard_enabled:
                service_config = llm_guard_config.get('service', {})
                base_url = service_config.get('base_url', 'http://localhost:8000')
                self.logger.info(f"  LLM Guard service URL: {base_url}")
                
                security_config = llm_guard_config.get('security', {})
                risk_threshold = security_config.get('risk_threshold', 0.6)
                self.logger.info(f"  Default risk threshold: {risk_threshold}")
                
                # Use default scanner lists since they're not in simplified config
                self.logger.info(f"  Available input scanners: 7 (default)")
                self.logger.info(f"  Available output scanners: 4 (default)")
            
            # Get safety configuration
            safety_config = self.config.get('safety', {})
            safety_enabled = _is_true_value(safety_config.get('enabled', False))
            safety_mode = safety_config.get('mode', 'strict')
            safety_moderator = safety_config.get('moderator')
            
            # Log safety information
            self.logger.info(f"Safety: {'enabled' if safety_enabled else 'disabled'}")
            if safety_enabled:
                self.logger.info(f"Safety mode: {safety_mode}")
                
                # Log moderator information if specified
                if safety_moderator:
                    self.logger.info(f"Safety moderator: {safety_moderator}")
                    
                    # Log moderator-specific configuration if available
                    moderators_config = self.config.get('moderators', {})
                    if safety_moderator in moderators_config:
                        moderator_config = moderators_config[safety_moderator]
                        model = moderator_config.get('model', 'unknown')
                        self.logger.info(f"Moderation model: {model}")
                        
                        # Log additional moderator settings if available
                        if 'temperature' in moderator_config:
                            self.logger.info(f"Moderation temperature: {moderator_config['temperature']}")
                        if 'max_tokens' in moderator_config:
                            self.logger.info(f"Moderation max tokens: {moderator_config['max_tokens']}")
                        if 'batch_size' in moderator_config:
                            self.logger.info(f"Moderation batch size: {moderator_config['batch_size']}")
                else:
                    self.logger.info("Safety moderator: not specified (will use inference provider)")

            # Log chat history information if in inference_only mode
            inference_only = _is_true_value(self.config.get('general', {}).get('inference_only', False))
            if inference_only:
                self._log_chat_history_configuration()
        except Exception as e:
            self.logger.error(f"Error logging service configurations: {str(e)}")
    
    def _log_chat_history_configuration(self) -> None:
        """Log chat history service configuration."""
        try:
            chat_history_config = self.config.get('chat_history', {})
            chat_history_enabled = _is_true_value(chat_history_config.get('enabled', True))
            self.logger.info(f"Chat History: {'enabled' if chat_history_enabled else 'disabled'}")
            
            if chat_history_enabled:
                self.logger.info(f"  - Default message limit: {chat_history_config.get('default_limit', 50)}")
                self.logger.info(f"  - Store metadata: {chat_history_config.get('store_metadata', True)}")
                self.logger.info(f"  - Retention days: {chat_history_config.get('retention_days', 90)}")
                self.logger.info(f"  - Session auto-generate: {chat_history_config.get('session', {}).get('auto_generate', True)}")
                self.logger.info(f"  - Max conversation messages: dynamically calculated based on inference provider context window")
        except Exception as e:
            self.logger.error(f"Error logging chat history configuration: {str(e)}")
    
    def _log_api_configurations(self) -> None:
        """Log API and security configuration details."""
        try:
            # Get language detection configuration
            language_detection_enabled = _is_true_value(self.config.get('general', {}).get('language_detection', True))
            self.logger.info(f"Language Detection: {'enabled' if language_detection_enabled else 'disabled'}")
            
            # Get session ID configuration
            session_config = self.config.get('general', {}).get('session_id', {})
            session_enabled = _is_true_value(session_config.get('required', False))
            session_header = session_config.get('header_name', 'X-Session-ID')
            self.logger.info(f"Session ID: {'enabled' if session_enabled else 'disabled'} (header: {session_header})")
            
            # Get API key configuration
            api_key_config = self.config.get('api_keys', {})
            api_key_enabled = _is_true_value(api_key_config.get('enabled', True))
            api_key_header = api_key_config.get('header_name', 'X-API-Key')
            self.logger.info(f"API Key: {'enabled' if api_key_enabled else 'disabled'} (header: {api_key_header})")
        except Exception as e:
            self.logger.error(f"Error logging API configurations: {str(e)}")
    
    def _log_model_information(self) -> None:
        """Log model configuration details."""
        try:
            # Log model information based on the selected inference provider
            inference_provider = self.config.get('general', {}).get('inference_provider', 'ollama')
            if inference_provider in self.config.get('inference', {}):
                model_name = self.config['inference'][inference_provider].get('model', 'unknown')
                self.logger.info(f"Server running with {model_name} model")
        except Exception as e:
            self.logger.error(f"Error logging model information: {str(e)}")
    
    def _log_runtime_information(self, app: FastAPI) -> None:
        """Log runtime-specific information when available."""
        try:
            # Log retriever information only if not in inference_only mode and retriever exists
            inference_only = _is_true_value(self.config.get('general', {}).get('inference_only', False))
            if not inference_only and hasattr(app.state, 'retriever') and app.state.retriever is not None:
                try:
                    self.logger.info(f"Confidence threshold: {app.state.retriever.confidence_threshold}")
                except AttributeError:
                    # Skip logging if retriever is not fully initialized
                    pass
            
            # Log chat history service status (always show, regardless of verbose)
            chat_history_loaded = hasattr(app.state, 'chat_history_service') and app.state.chat_history_service is not None
            self.logger.info(f"Chat History Service: {'loaded' if chat_history_loaded else 'not loaded'}")
            
            # Log moderator service status
            moderator_loaded = hasattr(app.state, 'moderator_service') and app.state.moderator_service is not None
            self.logger.info(f"Moderator Service: {'loaded' if moderator_loaded else 'not loaded'}")
            
        except Exception as e:
            self.logger.error(f"Error logging runtime information: {str(e)}")
    
    def _log_endpoint_information(self) -> None:
        """Log API endpoint information."""
        try:
            self.logger.info("API Endpoints:")
            self.logger.info("  - MCP Completion Endpoint: POST /v1/chat")
            self.logger.info("  - Health check: GET /health")
        except Exception as e:
            self.logger.error(f"Error logging endpoint information: {str(e)}")
    
    def _log_system_settings(self) -> None:
        """Log system-level settings."""
        try:
            verbose_enabled = _is_true_value(self.config.get('general', {}).get('verbose', False))
            self.logger.info(f"Verbose mode: {verbose_enabled}")
        except Exception as e:
            self.logger.error(f"Error logging system settings: {str(e)}")
    
    def generate_configuration_report(self) -> Dict[str, Any]:
        """
        Generate a structured configuration report for programmatic use.
        
        Returns:
            A dictionary containing structured configuration information
        """
        try:
            inference_only = _is_true_value(self.config.get('general', {}).get('inference_only', False))
            
            report = {
                'server_mode': {
                    'inference_only': inference_only,
                    'rag_enabled': not inference_only
                },
                'providers': {
                    'inference': self.config.get('general', {}).get('inference_provider', 'ollama')
                },
                'services': {
                    'llm_guard': {
                        'enabled': self._get_llm_guard_enabled_status(),
                        'base_url': self._get_llm_guard_base_url(),
                        'default_risk_threshold': self._get_llm_guard_risk_threshold(),
                        'fallback_behavior': self._get_llm_guard_fallback_behavior()
                    }
                },
                'api': {
                    'language_detection': _is_true_value(self.config.get('general', {}).get('language_detection', True)),
                    'session_id_required': _is_true_value(self.config.get('general', {}).get('session_id', {}).get('required', False)),
                    'api_key_enabled': _is_true_value(self.config.get('api_keys', {}).get('enabled', True))
                },
                'system': {
                    'verbose': _is_true_value(self.config.get('general', {}).get('verbose', False))
                }
            }
            
            # Add embedding info if not in inference_only mode
            if not inference_only:
                embedding_config = self.config.get('embedding', {})
                report['providers']['embedding'] = {
                    'enabled': _is_true_value(embedding_config.get('enabled', True)),
                    'provider': embedding_config.get('provider', 'ollama')
                }
            
            # Add chat history info if in inference_only mode
            if inference_only:
                chat_history_config = self.config.get('chat_history', {})
                report['services']['chat_history'] = {
                    'enabled': _is_true_value(chat_history_config.get('enabled', True)),
                    'default_limit': chat_history_config.get('default_limit', 50),
                    'retention_days': chat_history_config.get('retention_days', 90)
                }
            
            return report
        except Exception as e:
            self.logger.error(f"Error generating configuration report: {str(e)}")
            return {
                'error': f"Failed to generate configuration report: {str(e)}",
                'server_mode': {'inference_only': False, 'rag_enabled': True}
            }
    
    def _get_llm_guard_enabled_status(self) -> bool:
        """Get LLM Guard enabled status from either configuration structure"""
        llm_guard_config = self.config.get('llm_guard', {})
        if llm_guard_config:
            if 'enabled' in llm_guard_config:
                return llm_guard_config.get('enabled', False)
            else:
                return True
        return False
    
    def _get_llm_guard_base_url(self) -> str:
        """Get LLM Guard base URL from either configuration structure"""
        llm_guard_config = self.config.get('llm_guard', {})
        return llm_guard_config.get('service', {}).get('base_url', 'http://localhost:8000')
    
    def _get_llm_guard_risk_threshold(self) -> float:
        """Get LLM Guard risk threshold from either configuration structure"""
        llm_guard_config = self.config.get('llm_guard', {})
        return llm_guard_config.get('security', {}).get('risk_threshold', 0.6)
    
    def _get_llm_guard_fallback_behavior(self) -> str:
        """Get LLM Guard fallback behavior from either configuration structure"""
        llm_guard_config = self.config.get('llm_guard', {})
        return llm_guard_config.get('fallback', {}).get('on_error', 'allow')