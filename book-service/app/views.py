from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Book
from .serializers import BookSerializer

class BookListCreate(APIView):
    def get(self, request):
        # Get query parameters for filtering and search
        query = request.query_params.get('q', '')
        author = request.query_params.get('author', '')
        category = request.query_params.get('category', '')
        min_price = request.query_params.get('min_price', '')
        max_price = request.query_params.get('max_price', '')
        in_stock = request.query_params.get('in_stock', '')
        
        # Start with active books
        books = Book.objects.filter(is_active=True)
        
        # Search by title or ISBN
        if query:
            books = books.filter(
                Q(title__icontains=query) | 
                Q(isbn__icontains=query) |
                Q(description__icontains=query)
            )
        
        # Filter by author
        if author:
            books = books.filter(author__icontains=author)
        
        # Filter by category
        if category:
            books = books.filter(category__icontains=category)
        
        # Filter by price range
        if min_price:
            try:
                books = books.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                books = books.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Filter by stock availability
        if in_stock and in_stock.lower() == 'true':
            books = books.filter(stock__gt=0)
        
        # Sort by rating or creation date
        sort_by = request.query_params.get('sort', '-created_at')
        if sort_by in ['price', '-price', 'average_rating', '-average_rating', 'created_at', '-created_at']:
            books = books.order_by(sort_by)
        
        # Pagination
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 20)
        try:
            page = int(page)
            limit = int(limit)
            start = (page - 1) * limit
            end = start + limit
            total = books.count()
            books = books[start:end]
        except ValueError:
            pass
        
        serializer = BookSerializer(books, many=True)
        return Response({
            'total': total,
            'page': page,
            'limit': limit,
            'results': serializer.data
        })

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookDetail(APIView):
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk, is_active=True)
            serializer = BookSerializer(book)
            return Response(serializer.data)
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
            serializer = BookSerializer(book, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
            book.is_active = False
            book.save()
            return Response({"message": "Book deleted successfully"})
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class BookSearch(APIView):
    """Dedicated search endpoint with advanced filtering"""
    def get(self, request):
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {"error": "Search query is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(description__icontains=query),
            is_active=True
        )
        
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Book service is running"})
