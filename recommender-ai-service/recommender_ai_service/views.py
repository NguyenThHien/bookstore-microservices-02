from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, Avg
from collections import Counter
import requests
from .models import Recommendation, ViewHistory, PurchaseHistory, CustomerPreference
from .serializers import RecommendationSerializer, ViewHistorySerializer
import math

BOOK_SERVICE_URL = "http://book-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"

class RecommendationList(generics.ListAPIView):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

class RecommendationDetail(generics.RetrieveAPIView):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

class CustomerRecommendations(APIView):
    """Get stored recommendations for a customer"""
    def get(self, request, customer_id):
        try:
            recommendations = Recommendation.objects.get(customer_id=customer_id)
            serializer = RecommendationSerializer(recommendations)
            return Response(serializer.data)
        except Recommendation.DoesNotExist:
            return Response(
                {'recommended_book_ids': [], 'scores': {}, 'algorithm': 'none'},
                status=status.HTTP_200_OK
            )

class GenerateRecommendations(APIView):
    """Generate recommendations using multiple algorithms"""
    def post(self, request, customer_id):
        try:
            # Get customer view history
            view_history = ViewHistory.objects.filter(customer_id=customer_id).order_by('-viewed_at')[:50]
            
            # Get customer purchase history
            purchase_history = PurchaseHistory.objects.filter(customer_id=customer_id).order_by('-purchased_at')[:20]
            
            if not view_history and not purchase_history:
                # No history - recommend trending books
                return self._get_trending_recommendations(customer_id)
            
            # Collect viewed/purchased books and categories
            viewed_books = set(h.book_id for h in view_history)
            purchased_books = set(h.book_id for h in purchase_history)
            viewed_categories = [h.category for h in view_history if h.category]
            purchased_categories = [h.category for h in purchase_history if h.category]
            
            # Determine dominant categories
            all_categories = viewed_categories + purchased_categories
            category_counts = Counter(all_categories)
            top_categories = [cat[0] for cat in category_counts.most_common(3)]
            
            # Generate recommendations using content-based + collaborative filtering
            recommendations = self._generate_hybrid_recommendations(
                customer_id,
                viewed_books,
                purchased_books,
                top_categories
            )
            
            if not recommendations:
                # Fallback to trending
                return self._get_trending_recommendations(customer_id)
            
            # Store recommendations
            recommendation_obj, created = Recommendation.objects.update_or_create(
                customer_id=customer_id,
                defaults={
                    'recommended_book_ids': [r['book_id'] for r in recommendations],
                    'scores': {str(r['book_id']): r['score'] for r in recommendations},
                    'algorithm': 'hybrid',
                    'confidence': sum(r['score'] for r in recommendations) / len(recommendations),
                    'reason': f"Based on {len(top_categories)} preferred categories"
                }
            )
            
            serializer = RecommendationSerializer(recommendation_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_hybrid_recommendations(self, customer_id, viewed_books, purchased_books, categories):
        """Generate recommendations using hybrid approach"""
        try:
            # Fetch all books with matching categories
            all_books_response = requests.get(f"{BOOK_SERVICE_URL}/books/?limit=1000", timeout=5)
            
            if all_books_response.status_code != 200:
                return []
            
            all_books = all_books_response.json().get('results', [])
            
            scored_books = {}
            excluded_books = viewed_books | {1, 2, 3, 4, 5}  # Exclude viewed/test books
            
            for book in all_books:
                book_id = book.get('id')
                if book_id in excluded_books or not book.get('is_active'):
                    continue
                
                score = 0.0
                
                # Content-based: category matching (60% weight)
                if book.get('category') in categories:
                    score += 0.6 * (1 + categories.count(book.get('category')) * 0.1)
                
                # Popularity-based: rating and reviews (20% weight)
                avg_rating = book.get('average_rating', 0)
                review_count = book.get('review_count', 0)
                if avg_rating > 0:
                    score += 0.2 * (avg_rating / 5.0 * (1 + math.log(review_count + 1) / 10))
                
                # Stock availability (10% weight)
                if book.get('stock', 0) > 0:
                    score += 0.1
                
                # Price reasonableness (10% weight)
                price = float(book.get('price', 0))
                if 50000 <= price <= 500000:  # Vietnamese price range
                    score += 0.1
                
                if score > 0:
                    scored_books[book_id] = {
                        'book_id': book_id,
                        'title': book.get('title'),
                        'author': book.get('author'),
                        'score': score
                    }
            
            # Sort by score and pick top 10
            sorted_books = sorted(scored_books.values(), key=lambda x: x['score'], reverse=True)
            return sorted_books[:10]
        except Exception as e:
            print(f"Error generating hybrid recommendations: {str(e)}")
            return []
    
    def _get_trending_recommendations(self, customer_id):
        """Get trending/popular books when no history available"""
        try:
            # Fetch popular books (sorted by rating)
            books_response = requests.get(
                f"{BOOK_SERVICE_URL}/books/?sort=-average_rating&limit=10",
                timeout=5
            )
            
            if books_response.status_code != 200:
                return Response(
                    {'recommended_book_ids': [], 'scores': {}},
                    status=status.HTTP_200_OK
                )
            
            books = books_response.json().get('results', [])[:10]
            book_ids = [b['id'] for b in books]
            scores = {str(b['id']): b.get('average_rating', 0) / 5.0 for b in books}
            
            # Store trending recommendations
            Recommendation.objects.update_or_create(
                customer_id=customer_id,
                defaults={
                    'recommended_book_ids': book_ids,
                    'scores': scores,
                    'algorithm': 'popular',
                    'confidence': 0.7,
                    'reason': 'Popular books based on customer ratings'
                }
            )
            
            return Response({
                'recommended_book_ids': book_ids,
                'scores': scores,
                'algorithm': 'popular',
                'confidence': 0.7
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ViewHistoryCreate(generics.CreateAPIView):
    """Log a book view"""
    queryset = ViewHistory.objects.all()
    serializer_class = ViewHistorySerializer

class RecordPurchase(APIView):
    """Record a purchase for recommendation engine"""
    def post(self, request):
        customer_id = request.data.get('customer_id')
        book_id = request.data.get('book_id')
        category = request.data.get('category', '')
        price = request.data.get('price', 0)
        rating = request.data.get('rating', 0)
        
        if not customer_id or not book_id:
            return Response(
                {"error": "customer_id and book_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            purchase, created = PurchaseHistory.objects.update_or_create(
                customer_id=customer_id,
                book_id=book_id,
                defaults={
                    'category': category,
                    'price': price,
                    'rating': rating
                }
            )
            return Response(
                {"message": "Purchase recorded successfully"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class CustomerPreferenceUpdate(APIView):
    """Update customer preferences"""
    def post(self, request, customer_id):
        try:
            pref_data = {
                'preferred_categories': request.data.get('preferred_categories', []),
                'preferred_authors': request.data.get('preferred_authors', []),
                'price_preference': request.data.get('price_preference', 'any'),
                'rating_threshold': request.data.get('rating_threshold', 0.0),
            }
            
            preference, created = CustomerPreference.objects.update_or_create(
                customer_id=customer_id,
                defaults=pref_data
            )
            
            return Response(
                {"message": "Preferences updated"},
                status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Recommender-AI service healthy"}, status=status.HTTP_200_OK)
