from datetime import datetime
from typing import Dict, Any, Optional, Union
import json


class APIError(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ValidationError(APIError):
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__("VALIDATION_ERROR", message, details, 400)


class RateLimitError(APIError):
    def __init__(self, retry_after: int, quota_reset: Optional[str] = None):
        details = {"retry_after": retry_after}
        if quota_reset:
            details["quota_reset"] = quota_reset
        super().__init__("RATE_LIMITED", f"API quota exceeded. Try again in {retry_after} seconds.", details, 429)


class ServiceUnavailableError(APIError):
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__("SERVICE_UNAVAILABLE", message, {}, 503)


class WisdomQuote:
    def __init__(self, quote_id: str, quote: str, attribution: str, 
                 perspective: str, context: str, style: str = "inspirational",
                 created_at: Optional[datetime] = None, processing_time_ms: Optional[int] = None):
        self.quote_id = quote_id
        self.quote = quote
        self.attribution = attribution
        self.perspective = perspective
        self.context = context
        self.style = style
        self.created_at = created_at or datetime.utcnow()
        self.processing_time_ms = processing_time_ms

    def to_api_response(self, include_image_url: bool = True) -> Dict[str, Any]:
        response = {
            "quote_id": self.quote_id,
            "quote": self.quote,
            "attribution": self.attribution,
            "perspective": self.perspective,
            "context": self.context,
            "created_at": self.created_at.isoformat() + "Z",
            "metadata": {
                "style": self.style
            }
        }
        
        if include_image_url:
            response["image_url"] = f"https://app.vercel.app/api/v1/images/{self.quote_id}"
        
        if self.processing_time_ms is not None:
            response["metadata"]["processing_time_ms"] = self.processing_time_ms
            
        return response

    def to_mcp_response(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "text": f"{self.quote}\n\n— {self.attribution}",
            "metadata": {
                "quote_id": self.quote_id,
                "quote": self.quote,
                "attribution": self.attribution,
                "perspective": self.perspective,
                "context": self.context,
                "image_url": f"https://app.vercel.app/api/v1/images/{self.quote_id}"
            }
        }

    def to_web_format(self) -> Dict[str, Any]:
        return {
            "quote": self.quote,
            "attribution": self.attribution,
            "perspective": self.perspective,
            "context": self.context
        }

    @classmethod
    def from_legacy_response(cls, legacy_data: Dict[str, Any], quote_id: str, 
                           style: str = "inspirational", processing_time_ms: Optional[int] = None):
        return cls(
            quote_id=quote_id,
            quote=legacy_data["quote"],
            attribution=legacy_data["attribution"], 
            perspective=legacy_data["perspective"],
            context=legacy_data["context"],
            style=style,
            processing_time_ms=processing_time_ms
        )


class APIResponse:
    @staticmethod
    def success(data: Union[Dict[str, Any], WisdomQuote], status_code: int = 200) -> Dict[str, Any]:
        if isinstance(data, WisdomQuote):
            response_data = data.to_api_response()
        else:
            response_data = data
            
        return {
            "status_code": status_code,
            "headers": {
                "Content-Type": "application/json",
                "API-Version": "1.0",
                "Cache-Control": "no-cache"
            },
            "body": json.dumps(response_data)
        }

    @staticmethod
    def error(error: Union[APIError, Exception], status_code: Optional[int] = None) -> Dict[str, Any]:
        if isinstance(error, APIError):
            error_data = {
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "details": error.details
                }
            }
            status = error.status_code
        else:
            error_data = {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {}
                }
            }
            status = status_code or 500

        return {
            "status_code": status,
            "headers": {
                "Content-Type": "application/json",
                "API-Version": "1.0"
            },
            "body": json.dumps(error_data)
        }

    @staticmethod 
    def rate_limit(retry_after: int, quota_reset: Optional[str] = None) -> Dict[str, Any]:
        error = RateLimitError(retry_after, quota_reset)
        response = APIResponse.error(error)
        response["headers"]["Retry-After"] = str(retry_after)
        return response


class QuoteRequest:
    def __init__(self, data: Dict[str, Any]):
        self.input = self._validate_input(data.get('input'))
        self.style = self._validate_style(data.get('style'))
        self.include_image = data.get('include_image', True)

    def _validate_input(self, input_text: Any) -> str:
        if input_text is None:
            raise ValidationError("Input is required", "input")
        
        if not isinstance(input_text, str):
            raise ValidationError("Input must be a string", "input")
        
        cleaned = input_text.strip()
        if len(cleaned) == 0:
            raise ValidationError("Input too short (minimum 3 characters)", "input")
        
        if len(cleaned) < 3:
            raise ValidationError("Input too short (minimum 3 characters)", "input")
        
        if len(cleaned) > 500:
            raise ValidationError("Input too long (maximum 500 characters)", "input")
        
        return cleaned

    def _validate_style(self, style: Any) -> str:
        valid_styles = ["inspirational", "practical", "philosophical", "humorous"]
        
        if style is None:
            return "inspirational"
        
        if not isinstance(style, str):
            raise ValidationError("Style must be a string", "style")
        
        if style not in valid_styles:
            raise ValidationError(f"Invalid style. Must be one of: {', '.join(valid_styles)}", "style")
        
        return style


class ImageRequest:
    def __init__(self, data: Dict[str, Any]):
        self.quote_id = self._validate_quote_id(data.get('quote_id'))
        self.design = self._validate_design(data.get('design', 3))

    def _validate_quote_id(self, quote_id: Any) -> str:
        if quote_id is None:
            raise ValidationError("Quote ID is required", "quote_id")
        
        if not isinstance(quote_id, str):
            raise ValidationError("Quote ID must be a string", "quote_id")
        
        if len(quote_id.strip()) == 0:
            raise ValidationError("Quote ID cannot be empty", "quote_id")
        
        return quote_id

    def _validate_design(self, design: Any) -> int:
        if design is None:
            return 3
        
        try:
            design_int = int(design)
        except (ValueError, TypeError):
            raise ValidationError("Design must be an integer", "design")
        
        if design_int < 1 or design_int > 4:
            raise ValidationError("Design must be between 1 and 4", "design")
        
        return design_int