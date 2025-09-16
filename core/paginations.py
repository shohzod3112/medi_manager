import math

from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class CustomPagination(BasePagination):
    page_query_param = 'page'
    size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        page_size = int(request.GET.get(self.size_query_param, 10))
        page = int(request.GET.get(self.page_query_param, 1))
        start = (page - 1) * page_size
        end = start + page_size
        self.page = page
        self.page_size = page_size
        self.total = queryset.count()
        return list(queryset[start:end])

    def get_paginated_response(self, data):
        return Response({
            'count': self.total,
            'num_pages': math.ceil(self.total / self.page_size),
            'size': self.page_size,
            'results': data
        })
