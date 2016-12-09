from rest_framework import serializers, pagination

class RangeStart(serializers.Field):
        """
        Index of first item of current results set
        """
        def to_native(self, value):
            val = (value.paginator.per_page * value.number) - value.paginator.per_page + 1
            return val

class RangeEnd(serializers.Field):
        """
        Index of last item of current results set
        """
        def to_native(self, value):
            thispage = value.object_list.count()
            return (value.paginator.per_page * value.number) - (value.paginator.per_page - thispage)
            
class PageSize(serializers.Field):
        """
        Number of items per page
        """
        def to_native(self, value):
            return value.paginator.per_page

class PageTotal(serializers.Field):
        """
        Number of pages total
        """
        def to_native(self, value):
            return value.paginator.num_pages

class CustomPaginationSerializer(pagination.PaginationSerializer):
    """
    Override of default pagination serializer to include page range.
    """
    current_page = serializers.Field(source='number')
    range_start = RangeStart(source='*')
    range_end = RangeEnd(source='*')
    page_size = PageSize(source='*')
    page_total = PageTotal(source='*')


    