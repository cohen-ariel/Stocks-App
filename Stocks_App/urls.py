from django.contrib import admin
from django.urls import path,include
from Stocks_App import views

urlpatterns = [
path('', views.Home,name = 'Home'),
path('Home', views.Home,name = 'Home'),
path('Query_Results', views.Query_res, name= 'Query_Results'),
path('Add_Transaction', views.add_transactions, name= 'Add_Transaction'),
path('Buy_Stocks', views.buy_stocks, name= 'Buy_Stocks'),
]
