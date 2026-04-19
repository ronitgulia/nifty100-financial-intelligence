from django.urls import path
from django.shortcuts import render
from . import views


def home(request):
    return render(request, 'home/index.html')


def company_page(request, symbol):
    return render(request, 'company/detail.html', {'symbol': symbol})


urlpatterns = [
    path('', home, name='home'),
    path('company/<str:symbol>/', company_page, name='company-page'),
    path('companies/', views.company_list),
    path('companies/<str:symbol>/', views.company_detail),
    path('companies/<str:symbol>/profit-loss/', views.profit_loss),
    path('companies/<str:symbol>/balance-sheet/', views.balance_sheet),
    path('companies/<str:symbol>/cash-flow/', views.cash_flow),
    path('companies/<str:symbol>/ml-score/', views.ml_scores),
    path('companies/<str:symbol>/pros-cons/', views.pros_cons),
    path('sectors/', views.sector_list),
    path('top-companies/', views.top_companies),
]