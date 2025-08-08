from rest_framework.pagination import PageNumberPagination


class PageSizeLimitPagination(PageNumberPagination):
    """A class for applying a limit on the number of elements on a page"""

    page_size_query_param = 'limit'
    page_size = 6
