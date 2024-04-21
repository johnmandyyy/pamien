from django.urls import path
from . import views

urlpatterns = [
    path('pamine/',views.home, name='home'),
    path('', views.login_user, name='login'),
    path('login/', views.login_user, name='login'),
    path('signup/', views.signup, name='signup'),
    path('history/',views.history, name='history'),
    path('presignup/', views.presignup, name='presignup'),
    path('pamine/livepage/<int:id>/', views.livepage, name='livepage'),
    path('pamine/livepage/<int:id>/end/<str:live>', views.endLive, name='endLive'),
    path('pamine/livepage/<int:id>/order', views.createOrderAndUpdateInventory, name='createOrder'),
    path('pamine/setuplive/', views.livesetup, name='setuplive'),
    path('pamine/setupshopify/', views.shopifysetup, name='setupshopify'),
    path('logout/', views.logout_user, name="logout"),
]
