# Add this to your Django middleware

import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Log the exception
        logger.error(f"Exception occurred: {str(exception)}", exc_info=True)
        
        # Handle specific exceptions
        if isinstance(exception, PermissionDenied):
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        elif isinstance(exception, DatabaseError):
            return JsonResponse({
                'success': False,
                'error': 'Database error occurred'
            }, status=500)
        
        elif isinstance(exception, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid input'
            }, status=400)
        
        # Default error response
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)