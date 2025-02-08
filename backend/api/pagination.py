from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserPagination(PageNumberPagination):
    page_size = PER_PAGE
    page_size_query_param = 'limit'
    max_page_size = MAX_PER_PAGE
