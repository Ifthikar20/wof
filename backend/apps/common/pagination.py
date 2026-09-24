from rest_framework.pagination import CursorPagination


class FeedCursorPagination(CursorPagination):
    """
    Opaque cursor pagination: stable under inserts, no total counts, no page numbers and
    no client-controlled page size -- so there is no cheap way to enumerate the corpus.
    """

    page_size = 24
    ordering = "-published_at"
    page_size_query_param = None
    max_page_size = 24


class SmallCursorPagination(FeedCursorPagination):
    page_size = 20
    ordering = "-created_at"
