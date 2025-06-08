"""
WisdomService - New interface for wisdom quote generation

This service implements the strangler pattern to gradually migrate from 
direct openai_service.py calls to a clean, testable API interface.

MIGRATION STATUS: Phase 1 - Creating New Interface
- Uses legacy openai_service.py internally 
- Adds response formatting and rate limiting integration
- Maintains 100% backward compatibility during transition
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from lib.api.response_formatter import (
    WisdomQuote, ValidationError, ServiceUnavailableError,
    QuoteRequest
)


class WisdomService:
    """
    Core wisdom quote generation service using strangler pattern.
    
    During migration, this service wraps the legacy openai_service.py
    to provide a clean interface for both API and web usage.
    """
    
    def __init__(self, rate_limiter=None):
        """
        Initialize wisdom service.
        
        Args:
            rate_limiter: Optional BudgetBasedRateLimiter instance for cost tracking
        """
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)
    
    def generate_quote(self, input_text: str, style: str = "inspirational", 
                      client_ip: str = "127.0.0.1", user_agent: str = "",
                      track_cost: bool = True) -> WisdomQuote:
        """
        Generate a wisdom quote based on user input.
        
        This method implements the strangler pattern by:
        1. Using new validation and response formatting
        2. Calling legacy openai_service.py for actual generation
        3. Converting legacy response to new WisdomQuote format
        4. Integrating with new rate limiting and cost tracking
        
        Args:
            input_text: User's situation, feeling, or challenge
            style: Preferred wisdom style (inspirational, practical, philosophical, humorous)
            client_ip: Client IP for rate limiting (default: localhost)
            user_agent: Client User-Agent for AI agent detection
            track_cost: Whether to track costs with rate limiter
            
        Returns:
            WisdomQuote: Formatted quote with all metadata
            
        Raises:
            ValidationError: Invalid input parameters
            ServiceUnavailableError: OpenAI API unavailable and fallback failed
        """
        start_time = datetime.utcnow()
        
        # STEP 1: Input validation using new system
        request_data = {"input": input_text, "style": style}
        try:
            quote_request = QuoteRequest(request_data)
            validated_input = quote_request.input
            validated_style = quote_request.style
        except ValidationError:
            raise  # Re-raise validation errors
        
        self.logger.info(f"WisdomService.generate_quote called with input: '{validated_input[:50]}...'")
        
        # STEP 2: Check cache using legacy cache logic (for now)
        input_hash = self._create_input_hash(validated_input)
        cached_quote = self._get_cached_quote_by_hash(input_hash)
        
        if cached_quote:
            self.logger.info(f"Cache hit for input hash: {input_hash[:8]}...")
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Convert cached data to new format
            return self._convert_legacy_to_wisdom_quote(
                cached_quote["legacy_data"], 
                cached_quote["quote_id"],
                validated_style,
                processing_time
            )
        
        # STEP 3: Generate new quote using legacy service
        try:
            # Import legacy service (strangler pattern - will be removed in Phase 4)
            from openai_service import get_wisdom_quotes
            
            self.logger.info("Cache miss - calling legacy openai_service.get_wisdom_quotes()")
            legacy_quotes = get_wisdom_quotes(validated_input)
            
            if not legacy_quotes or len(legacy_quotes) == 0:
                raise ServiceUnavailableError("No quotes generated from OpenAI service")
            
            # STEP 4: Store in cache using legacy cache format (for now)
            quote_cache_id = self._store_quotes_in_cache(input_hash, validated_input, legacy_quotes)
            
            # STEP 5: Track costs with rate limiter if provided
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            if track_cost and self.rate_limiter:
                # Estimate cost based on input/output length (approximation for now)
                estimated_cost = self._estimate_openai_cost(validated_input, legacy_quotes)
                self.rate_limiter.record_request(client_ip, user_agent, estimated_cost)
                self.logger.info(f"Recorded request cost: ${estimated_cost:.6f}")
            
            # STEP 6: Convert to new format and return first quote
            first_quote = legacy_quotes[0]
            quote_id = f"{quote_cache_id}_0"  # Legacy format: cache_id_quote_index
            
            wisdom_quote = self._convert_legacy_to_wisdom_quote(
                first_quote, quote_id, validated_style, processing_time
            )
            
            self.logger.info(f"Successfully generated quote {quote_id} in {processing_time}ms")
            return wisdom_quote
            
        except Exception as e:
            self.logger.error(f"Error in quote generation: {str(e)}")
            if "openai" in str(e).lower() or "api" in str(e).lower():
                raise ServiceUnavailableError(f"Quote generation service temporarily unavailable: {str(e)}")
            else:
                raise ServiceUnavailableError(f"Unexpected error: {str(e)}")
    
    def get_cached_quote(self, quote_id: str) -> Optional[WisdomQuote]:
        """
        Retrieve a cached quote by ID.
        
        Args:
            quote_id: Quote ID in format "cache_id_quote_index"
            
        Returns:
            WisdomQuote if found, None otherwise
        """
        try:
            # Parse legacy quote ID format
            if '_' not in quote_id:
                self.logger.warning(f"Invalid quote ID format: {quote_id}")
                return None
            
            cache_id, quote_index = quote_id.split('_', 1)
            quote_index = int(quote_index)
            
            # Use legacy cache retrieval (for now)
            cached_data = self._get_cached_quote_by_cache_id(cache_id, quote_index)
            if not cached_data:
                return None
            
            return self._convert_legacy_to_wisdom_quote(
                cached_data["legacy_data"],
                quote_id,
                "inspirational",  # Default style for cached quotes
                None  # No processing time for cached quotes
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached quote {quote_id}: {str(e)}")
            return None
    
    def _create_input_hash(self, input_text: str) -> str:
        """Create SHA256 hash of input text (legacy compatibility)"""
        return hashlib.sha256(input_text.encode()).hexdigest()
    
    def _get_cached_quote_by_hash(self, input_hash: str) -> Optional[Dict]:
        """
        Check if quotes for this input hash exist in cache.
        
        Returns dict with 'legacy_data' and 'quote_id' if found, None otherwise.
        """
        try:
            # Import models (strangler pattern - using legacy cache for now)
            from models import QuoteCache
            
            existing_cache = QuoteCache.query.filter_by(input_hash=input_hash).first()
            if not existing_cache:
                return None
            
            # Parse legacy cache format
            quotes_data = json.loads(existing_cache.response_data)
            if not quotes_data or len(quotes_data) == 0:
                return None
            
            # Return first quote (for now - API will return all quotes later)
            return {
                "legacy_data": quotes_data[0],
                "quote_id": f"{existing_cache.id}_0"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking cache: {str(e)}")
            return None
    
    def _get_cached_quote_by_cache_id(self, cache_id: str, quote_index: int) -> Optional[Dict]:
        """Retrieve specific quote by cache ID and index"""
        try:
            from models import QuoteCache
            
            quote_cache = QuoteCache.query.get(cache_id)
            if not quote_cache:
                return None
            
            quotes_data = json.loads(quote_cache.response_data)
            if quote_index >= len(quotes_data):
                return None
            
            return {
                "legacy_data": quotes_data[quote_index],
                "quote_id": f"{cache_id}_{quote_index}"
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving cache {cache_id}[{quote_index}]: {str(e)}")
            return None
    
    def _store_quotes_in_cache(self, input_hash: str, user_input: str, quotes_data: List[Dict]) -> int:
        """Store quotes in legacy cache format and return cache ID"""
        try:
            from models import QuoteCache
            from api.index import db
            
            quote_cache = QuoteCache(
                input_hash=input_hash,
                user_input=user_input,
                response_data=json.dumps(quotes_data)
            )
            db.session.add(quote_cache)
            db.session.commit()
            
            self.logger.info(f"Stored {len(quotes_data)} quotes in cache ID: {quote_cache.id}")
            return quote_cache.id
            
        except Exception as e:
            self.logger.error(f"Error storing quotes in cache: {str(e)}")
            # Return a dummy ID if caching fails (quote generation can still succeed)
            return 0
    
    def _convert_legacy_to_wisdom_quote(self, legacy_data: Dict, quote_id: str, 
                                       style: str, processing_time_ms: Optional[int]) -> WisdomQuote:
        """Convert legacy quote format to new WisdomQuote object"""
        return WisdomQuote.from_legacy_response(
            legacy_data=legacy_data,
            quote_id=quote_id,
            style=style,
            processing_time_ms=processing_time_ms
        )
    
    def _estimate_openai_cost(self, input_text: str, quotes: List[Dict]) -> float:
        """
        Estimate OpenAI API cost based on input/output length.
        
        This is a rough approximation for rate limiting purposes.
        In production, you'd want to use actual token counts from the API response.
        """
        # Rough estimation: gpt-4o-mini pricing
        # Input: ~150 tokens (system prompt) + user input
        # Output: ~200 tokens per quote
        
        input_tokens = len(input_text.split()) + 150  # Rough approximation
        output_tokens = sum(len((q.get('quote', '') + q.get('attribution', '') + 
                                q.get('perspective', '') + q.get('context', '')).split()) 
                           for q in quotes)
        
        # gpt-4o-mini pricing (as of 2024): $0.000150/1K input tokens, $0.000600/1K output tokens
        input_cost = (input_tokens / 1000) * 0.000150
        output_cost = (output_tokens / 1000) * 0.000600
        
        total_cost = input_cost + output_cost
        self.logger.debug(f"Cost estimation: {input_tokens} input + {output_tokens} output tokens = ${total_cost:.6f}")
        
        return total_cost


# MIGRATION MARKER: This service is in PHASE 1 - Creating New Interface
# 
# CURRENT STATE:
# - Uses legacy openai_service.py internally ✓
# - Provides new WisdomQuote interface ✓  
# - Integrates with rate limiting ✓
# - Maintains legacy cache compatibility ✓
#
# NEXT PHASE: Add feature flag and parallel operation testing
# DEPENDENCIES: Still requires openai_service.py, models.py, api.index.db
# ROLLBACK: Can be removed without affecting existing routes.py