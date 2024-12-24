from rest_framework.pagination import PageNumberPagination


class CustomUserPagination(PageNumberPagination):
    page_size = 10  # Количество объектов на странице по умолчанию
    page_size_query_param = 'limit'
    max_page_size = 100
