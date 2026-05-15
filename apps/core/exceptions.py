"""
Custom exception handlers for the DRF backend.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that logs errors and formats responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error
        logger.error(f"API Error: {exc.__class__.__name__} - {str(exc)}")
        return response
    
    # Handle other exceptions
    logger.error(f"Unhandled Exception: {exc.__class__.__name__} - {str(exc)}", exc_info=True)
    
    return Response(
        {
            'error': 'An unexpected error occurred',
            'detail': str(exc) if settings.DEBUG else None,
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


class CustomValidationError(Exception):
    """Custom validation error with detailed message."""
    def __init__(self, detail, field_errors=None):
        self.detail = detail
        self.field_errors = field_errors or {}
        super().__init__(detail)
