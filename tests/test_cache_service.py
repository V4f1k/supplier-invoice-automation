"""Tests for cache service"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.cache_service import CacheService


class TestCacheService:
    """Test cases for CacheService"""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance for testing"""
        return CacheService()
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        client = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service, mock_redis_client):
        """Test cache get with existing key"""
        # Setup
        test_key = "test_hash_123"
        test_value = {"text": "sample text", "filename": "test.pdf"}
        mock_redis_client.get.return_value = json.dumps(test_value)
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.get(test_key)
            
            # Assert
            assert result == test_value
            mock_redis_client.get.assert_called_once_with(test_key)
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service, mock_redis_client):
        """Test cache get with non-existing key"""
        # Setup
        test_key = "nonexistent_key"
        mock_redis_client.get.return_value = None
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.get(test_key)
            
            # Assert
            assert result is None
            mock_redis_client.get.assert_called_once_with(test_key)
    
    @pytest.mark.asyncio
    async def test_set_success(self, cache_service, mock_redis_client):
        """Test cache set with valid data"""
        # Setup
        test_key = "test_hash_456"
        test_value = {"text": "sample text", "filename": "test.pdf"}
        mock_redis_client.setex.return_value = True
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.set(test_key, test_value)
            
            # Assert
            assert result is True
            mock_redis_client.setex.assert_called_once_with(
                test_key, 86400, json.dumps(test_value)
            )
    
    @pytest.mark.asyncio
    async def test_set_failure(self, cache_service, mock_redis_client):
        """Test cache set failure"""
        # Setup
        test_key = "test_hash_789"
        test_value = {"text": "sample text", "filename": "test.pdf"}
        mock_redis_client.setex.return_value = False
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.set(test_key, test_value)
            
            # Assert
            assert result is False
            mock_redis_client.setex.assert_called_once_with(
                test_key, 86400, json.dumps(test_value)
            )
    
    @pytest.mark.asyncio
    async def test_check_exists(self, cache_service, mock_redis_client):
        """Test check method with existing key"""
        # Setup
        test_key = "existing_key"
        mock_redis_client.exists.return_value = 1
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.check(test_key)
            
            # Assert
            assert result is True
            mock_redis_client.exists.assert_called_once_with(test_key)
    
    @pytest.mark.asyncio
    async def test_check_not_exists(self, cache_service, mock_redis_client):
        """Test check method with non-existing key"""
        # Setup
        test_key = "nonexistent_key"
        mock_redis_client.exists.return_value = 0
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.check(test_key)
            
            # Assert
            assert result is False
            mock_redis_client.exists.assert_called_once_with(test_key)
    
    @pytest.mark.asyncio
    async def test_get_error_handling(self, cache_service, mock_redis_client):
        """Test error handling in get method"""
        # Setup
        test_key = "error_key"
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.get(test_key)
            
            # Assert
            assert result is None
    
    @pytest.mark.asyncio
    async def test_set_error_handling(self, cache_service, mock_redis_client):
        """Test error handling in set method"""
        # Setup
        test_key = "error_key"
        test_value = {"text": "sample text"}
        mock_redis_client.setex.side_effect = Exception("Redis connection error")
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            result = await cache_service.set(test_key, test_value)
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_ttl_value(self, cache_service, mock_redis_client):
        """Test that TTL is set to 24 hours (86400 seconds)"""
        # Setup
        test_key = "ttl_test_key"
        test_value = {"text": "sample text"}
        mock_redis_client.setex.return_value = True
        
        with patch.object(cache_service, '_get_client', return_value=mock_redis_client):
            # Execute
            await cache_service.set(test_key, test_value)
            
            # Assert TTL is 24 hours
            mock_redis_client.setex.assert_called_once_with(
                test_key, 86400, json.dumps(test_value)
            )