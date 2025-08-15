import logging
logger = logging.getLogger(__name__)

class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error("未処理の例外: %s", str(e), exc_info=True)
            raise  # 例外を再スローして Django に処理させる