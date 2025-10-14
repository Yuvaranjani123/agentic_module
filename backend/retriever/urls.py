from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('query/', views.query_document, name='query_document'),
    path('evaluation-summary/', views.evaluation_summary, name='evaluation_summary'),
    # Add more endpoints as needed
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)