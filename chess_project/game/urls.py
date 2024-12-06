from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.home, name='home'),
    path('history/', views.history, name='history'),
    path('rules/', views.rules, name='rules'),
    path('about/', views.about, name='about'),
    path('home/', views.home, name='home'),
    path('game/<int:game_id>/', views.game_view, name='game_view'), 
    path('<int:game_id>/join/', views.join_game, name='join_game'),  

    path('edit-game/<int:game_id>/', views.edit_game, name='edit_game'),
    path('delete-game/<int:game_id>/', views.delete_game, name='delete_game'),
    path('game/<int:game_id>/exit/', views.exit_game, name='exit_game'),

]
