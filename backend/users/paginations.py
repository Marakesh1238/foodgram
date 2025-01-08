from rest_framework.pagination import PageNumberPagination

from api.constants import MAX_PER_PAGE, PER_PAGE


class CustomUserPagination(PageNumberPagination):
    page_size = PER_PAGE  # Количество объектов на странице по умолчанию
    page_size_query_param = 'limit'
    max_page_size = MAX_PER_PAGE
