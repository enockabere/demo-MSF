from django.urls import path
from . import views

urlpatterns = [
    path('Approve', views.Approve.as_view(), name="approve"),
    path('ApproveData/<str:pk>', views.ApproveDetails.as_view(), name='ApproveData'),
    path('Approved/<str:pk>', views.All_Approved, name='All_Approved'),
    path('Rejected/<str:pk>', views.Rejected, name='Rejected'),
    path('getDocs/<str:pk>/<str:id>/', views.viewDocs, name='getDocs'),
]
