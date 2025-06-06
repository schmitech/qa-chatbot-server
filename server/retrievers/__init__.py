"""
Retriever package for handling different types of data retrieval implementations.
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Initializing retrievers package")

from .base.base_retriever import BaseRetriever, RetrieverFactory
from .base.abstract_vector_retriever import AbstractVectorRetriever
from .base.sql_retriever import AbstractSQLRetriever
from .adapters.domain_adapters import DocumentAdapterFactory

# Import implementations to register them
try:
    # Import vector database implementations
    from .implementations.vector import (
        ChromaRetriever,
        MilvusRetriever,
        PineconeRetriever,
        ElasticsearchRetriever,
        RedisRetriever
    )
    
    # Import QA specializations
    from .implementations.qa import (
        QAChromaRetriever,
        QASSQLRetriever
    )
    
    logger.info("Successfully imported vector retriever implementations")
except ImportError as e:
    logger.warning(f"Some vector retrievers could not be imported: {e}")

# Import SQL implementations
try:
    from .implementations.relational import (
        SQLiteRetriever,
        PostgreSQLRetriever,
        MySQLRetriever
    )
    
    logger.info("Successfully imported SQL retriever implementations")
except ImportError as e:
    logger.warning(f"Some SQL retrievers could not be imported: {e}")

# Expose main interfaces
__all__ = [
    'BaseRetriever',
    'RetrieverFactory',
    'AbstractVectorRetriever',
    'AbstractSQLRetriever',
    'DocumentAdapterFactory',
    # Vector implementations
    'ChromaRetriever',
    'MilvusRetriever', 
    'PineconeRetriever',
    'ElasticsearchRetriever',
    'RedisRetriever',
    # Relational implementations
    'SQLiteRetriever',
    'PostgreSQLRetriever',
    'MySQLRetriever',
    # QA specializations
    'QAChromaRetriever',
    'QASSQLRetriever'
]

# Import implementations to register them
# from .implementations import QAChromaRetriever
# from .implementations import QASqliteRetriever
# from .adapters.qa import QARetriever

# # Force import our specialized adapters to ensure registration
# try:
#     from .adapters.qa.chroma_qa_adapter import ChromaQAAdapter
#     logger.info("Successfully imported ChromaQAAdapter through retrievers/__init__.py")
# except ImportError as e:
#     logger.error(f"Error importing ChromaQAAdapter: {str(e)}")