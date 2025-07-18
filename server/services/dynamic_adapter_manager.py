"""
Dynamic Adapter Manager Service for handling on-demand adapter loading.

This service replaces the static single adapter initialization with a dynamic
system that loads adapters based on API key configurations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class DynamicAdapterManager:
    """
    Manages dynamic loading and caching of adapters based on API key configurations.
    
    This service:
    - Loads adapters on-demand based on adapter names
    - Caches initialized adapters for performance
    - Handles adapter lifecycle and cleanup
    - Provides thread-safe access to adapters
    """
    
    def __init__(self, config: Dict[str, Any], app_state=None):
        """
        Initialize the Dynamic Adapter Manager.
        
        Args:
            config: Application configuration
            app_state: FastAPI application state for accessing services
        """
        self.config = config
        self.app_state = app_state
        self.logger = logger
        self.verbose = config.get('general', {}).get('verbose', False)
        
        # Cache for initialized adapters
        self._adapter_cache: Dict[str, Any] = {}
        self._adapter_locks: Dict[str, threading.Lock] = {}
        self._cache_lock = threading.Lock()
        
        # Thread pool for adapter initialization
        self._thread_pool = ThreadPoolExecutor(max_workers=5)
        
        # Track loaded adapter configurations
        self._adapter_configs: Dict[str, Dict[str, Any]] = {}
        self._load_adapter_configs()
        
        # Set to track which adapters are currently being initialized
        self._initializing_adapters: Set[str] = set()
        
        self.logger.info("Dynamic Adapter Manager initialized")
        
    def _load_adapter_configs(self):
        """Load adapter configurations from config."""
        adapter_configs = self.config.get('adapters', [])
        
        for adapter_config in adapter_configs:
            adapter_name = adapter_config.get('name')
            if adapter_name:
                self._adapter_configs[adapter_name] = adapter_config
                if self.verbose:
                    self.logger.info(f"Loaded adapter config: {adapter_name}")
        
        self.logger.info(f"Loaded {len(self._adapter_configs)} adapter configurations")
    
    async def get_adapter(self, adapter_name: str) -> Any:
        """
        Get an adapter instance by name, loading it if necessary.
        
        Args:
            adapter_name: Name of the adapter to retrieve
            
        Returns:
            The initialized adapter instance
            
        Raises:
            ValueError: If adapter configuration is not found
            Exception: If adapter initialization fails
        """
        if not adapter_name:
            raise ValueError("Adapter name cannot be empty")
        
        # Check if adapter is already cached
        if adapter_name in self._adapter_cache:
            if self.verbose:
                self.logger.debug(f"Using cached adapter: {adapter_name}")
            return self._adapter_cache[adapter_name]
        
        # Check if adapter is currently being initialized
        with self._cache_lock:
            if adapter_name in self._initializing_adapters:
                # Wait for initialization to complete
                while adapter_name in self._initializing_adapters:
                    await asyncio.sleep(0.1)
                
                # Check cache again after waiting
                if adapter_name in self._adapter_cache:
                    return self._adapter_cache[adapter_name]
            
            # Mark adapter as being initialized
            self._initializing_adapters.add(adapter_name)
        
        try:
            # Load the adapter
            adapter = await self._load_adapter(adapter_name)
            
            # Cache the adapter
            with self._cache_lock:
                self._adapter_cache[adapter_name] = adapter
                # Create a lock for this adapter for future thread-safe operations
                self._adapter_locks[adapter_name] = threading.Lock()
            
            self.logger.info(f"Successfully loaded and cached adapter: {adapter_name}")
            return adapter
            
        except Exception as e:
            self.logger.error(f"Failed to load adapter {adapter_name}: {str(e)}")
            raise
        finally:
            # Remove from initializing set
            with self._cache_lock:
                self._initializing_adapters.discard(adapter_name)
    
    async def _load_adapter(self, adapter_name: str) -> Any:
        """Load and initialize an adapter asynchronously"""
        # Get adapter configuration
        adapter_config = self._adapter_configs.get(adapter_name)
        if not adapter_config:
            raise ValueError(f"No adapter configuration found for: {adapter_name}")
        
        # Run the import and initialization in a thread pool to prevent blocking
        loop = asyncio.get_event_loop()
        
        def _sync_load():
            # This runs in a thread, so it won't block the event loop
            implementation = adapter_config.get('implementation')
            datasource = adapter_config.get('datasource')
            adapter_type = adapter_config.get('adapter')
            
            # Import the retriever class
            module_path, class_name = implementation.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            retriever_class = getattr(module, class_name)
            
            # Create domain adapter
            from retrievers.adapters.registry import ADAPTER_REGISTRY
            adapter_config_params = adapter_config.get('config', {})
            domain_adapter = ADAPTER_REGISTRY.create(
                adapter_type='retriever',
                datasource=datasource,
                adapter_name=adapter_type,
                **adapter_config_params
            )
            
            # Create retriever instance
            retriever = retriever_class(
                config=self.config,
                domain_adapter=domain_adapter
            )
            
            return retriever
        
        # Load adapter in thread pool
        retriever = await loop.run_in_executor(self._thread_pool, _sync_load)
        
        # Initialize the retriever (if it's async)
        if hasattr(retriever, 'initialize'):
            if asyncio.iscoroutinefunction(retriever.initialize):
                await retriever.initialize()
            else:
                await loop.run_in_executor(self._thread_pool, retriever.initialize)
        
        return retriever
    
    def get_available_adapters(self) -> list[str]:
        """
        Get list of available adapter names.
        
        Returns:
            List of adapter names that can be loaded
        """
        return list(self._adapter_configs.keys())
    
    def get_cached_adapters(self) -> list[str]:
        """
        Get list of currently cached adapter names.
        
        Returns:
            List of adapter names that are currently cached
        """
        return list(self._adapter_cache.keys())
    
    async def preload_adapter(self, adapter_name: str) -> None:
        """
        Preload an adapter into cache.
        
        Args:
            adapter_name: Name of the adapter to preload
        """
        try:
            await self.get_adapter(adapter_name)
            self.logger.info(f"Preloaded adapter: {adapter_name}")
        except Exception as e:
            self.logger.error(f"Failed to preload adapter {adapter_name}: {str(e)}")
    
    async def preload_all_adapters(self, timeout_per_adapter: float = 30.0) -> Dict[str, Any]:
        """
        Preload all adapters in parallel with timeout protection.
        
        Args:
            timeout_per_adapter: Maximum time to wait for each adapter to load
            
        Returns:
            Dict with preload results for each adapter
        """
        available_adapters = self.get_available_adapters()
        if not available_adapters:
            return {}
        
        self.logger.info(f"Preloading {len(available_adapters)} adapters in parallel...")
        
        # Create tasks for parallel loading
        async def load_adapter_with_timeout(adapter_name: str):
            try:
                # Load adapter with timeout
                adapter = await asyncio.wait_for(
                    self.get_adapter(adapter_name),
                    timeout=timeout_per_adapter
                )
                return {
                    "adapter_name": adapter_name,
                    "success": True,
                    "message": "Preloaded successfully"
                }
            except asyncio.TimeoutError:
                return {
                    "adapter_name": adapter_name,
                    "success": False,
                    "error": f"Timeout after {timeout_per_adapter}s"
                }
            except Exception as e:
                return {
                    "adapter_name": adapter_name,
                    "success": False,
                    "error": str(e)
                }
        
        # Run all adapter loading tasks in parallel
        tasks = [load_adapter_with_timeout(name) for name in available_adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        preload_results = {}
        successful_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                # This shouldn't happen due to exception handling in load_adapter_with_timeout
                self.logger.error(f"Unexpected exception in adapter preloading: {result}")
                continue
                
            adapter_name = result["adapter_name"]
            preload_results[adapter_name] = result
            
            if result["success"]:
                successful_count += 1
                self.logger.info(f"✅ {adapter_name}: {result['message']}")
            else:
                self.logger.warning(f"❌ {adapter_name}: {result['error']}")
        
        self.logger.info(f"Adapter preloading completed: {successful_count}/{len(available_adapters)} successful")
        
        return preload_results
    
    async def remove_adapter(self, adapter_name: str) -> bool:
        """
        Remove an adapter from cache and clean up resources.
        
        Args:
            adapter_name: Name of the adapter to remove
            
        Returns:
            True if adapter was removed, False if not found
        """
        with self._cache_lock:
            if adapter_name not in self._adapter_cache:
                return False
            
            adapter = self._adapter_cache.pop(adapter_name)
            self._adapter_locks.pop(adapter_name, None)
        
        # Try to close the adapter if it has a close method
        try:
            if hasattr(adapter, 'close'):
                if asyncio.iscoroutinefunction(adapter.close):
                    await adapter.close()
                else:
                    adapter.close()
        except Exception as e:
            self.logger.warning(f"Error closing adapter {adapter_name}: {str(e)}")
        
        self.logger.info(f"Removed adapter from cache: {adapter_name}")
        return True
    
    async def clear_cache(self) -> None:
        """Clear all cached adapters and clean up resources."""
        adapter_names = list(self._adapter_cache.keys())
        
        for adapter_name in adapter_names:
            await self.remove_adapter(adapter_name)
        
        self.logger.info("Cleared all adapters from cache")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the adapter manager.
        
        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "available_adapters": len(self._adapter_configs),
            "cached_adapters": len(self._adapter_cache),
            "initializing_adapters": len(self._initializing_adapters),
            "adapter_configs": list(self._adapter_configs.keys()),
            "cached_adapter_names": list(self._adapter_cache.keys())
        }
    
    async def close(self) -> None:
        """Clean up all resources."""
        # Clear all cached adapters
        await self.clear_cache()
        
        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)
        
        self.logger.info("Dynamic Adapter Manager closed")


class AdapterProxy:
    """
    Proxy object that provides a retriever-like interface for the dynamic adapter manager.
    
    This allows LLM clients to use the adapter manager as if it were a single retriever,
    while actually routing to the appropriate adapter based on the adapter name.
    """
    
    def __init__(self, adapter_manager: DynamicAdapterManager):
        """
        Initialize the adapter proxy.
        
        Args:
            adapter_manager: The dynamic adapter manager instance
        """
        self.adapter_manager = adapter_manager
        self.logger = logger
    
    async def get_relevant_context(self, 
                                   query: str, 
                                   adapter_name: str,
                                   api_key: Optional[str] = None,
                                   **kwargs) -> list[Dict[str, Any]]:
        """
        Get relevant context using the specified adapter.
        
        Args:
            query: The user's query
            adapter_name: Name of the adapter to use
            api_key: Optional API key (for backward compatibility)
            **kwargs: Additional parameters
            
        Returns:
            List of relevant context items
        """
        if not adapter_name:
            raise ValueError("Adapter name is required")
        
        try:
            # Get the appropriate adapter
            adapter = await self.adapter_manager.get_adapter(adapter_name)
            
            # Call the adapter's get_relevant_context method
            # Pass api_key for compatibility but prioritize adapter_name routing
            return await adapter.get_relevant_context(
                query=query,
                api_key=api_key,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Error getting context from adapter {adapter_name}: {str(e)}")
            return []
    
    async def initialize(self) -> None:
        """Initialize method for compatibility."""
        # The adapter manager handles initialization of individual adapters
        pass
    
    async def close(self) -> None:
        """Close method for compatibility."""
        await self.adapter_manager.close() 