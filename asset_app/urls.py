from django.urls import path
from . import views,api_view


app_name = 'asset_app'
urlpatterns = [
    path('',views.AssetsListView.as_view(), name='assets-list'),
    path('asset/<int:pk>/detail/', views.AssetsDetailView.as_view(), name='assets-detail'),
    path('assets/new/',views.AssetsCreateView.as_view(), name='assets-create'),
    path('assign/<int:pk>/',views.AssetAssignView.as_view(), name='asset-assign'),
    path('asset/claim/', views.AssetClaimView.as_view(), name='asset-claim'),
    path('approve-notification/<int:notification_id>/', views.AssetClaimView.as_view(), name='approve-notification'),
    path('asset/<int:asset_id>/unclaim/',views.AssetUnclaimView.as_view(), name='asset-unclaim'),
    path('assets/<int:pk>/update/',views.AssetUpdateView.as_view(), name='asset-update'),
    path('assets/<int:pk>/delete/', views.AssetDeleteView.as_view(), name='asset-delete'),
    path('searchassets/', views.assetssearch, name='assetssearch'),

    path('api/asset/<int:pk>/detail/', api_view.AssetDetailAPIView.as_view(), name='asset-detail-api'),

]
