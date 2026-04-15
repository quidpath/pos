"""
Shared pagination helper for DRF-based microservices.
Returns a consistent response dict: {count, results, page, page_size, total_pages}
"""
from django.core.paginator import Paginator, EmptyPage

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 200


def paginate_qs(queryset, request):
    """
    Paginate a QuerySet using ?page and ?page_size query params.
    Returns (page_obj_list, meta_dict).
    """
    try:
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.GET.get("page_size", DEFAULT_PAGE_SIZE))))
    except (ValueError, TypeError):
        page_size = DEFAULT_PAGE_SIZE

    try:
        page_num = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page_num = 1

    paginator = Paginator(queryset, page_size)
    try:
        page = paginator.page(page_num)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page.object_list, {
        "count": paginator.count,
        "page": page.number,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
    }
