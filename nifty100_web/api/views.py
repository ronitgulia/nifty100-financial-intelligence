from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Company, ProfitLoss, BalanceSheet, CashFlow, MLScore, ProsCons
from .serializers import (
    CompanySerializer, CompanyDetailSerializer,
    ProfitLossSerializer, BalanceSheetSerializer,
    CashFlowSerializer, MLScoreSerializer, ProsConsSerializer
)


def home(request):
    return render(request, 'home/index.html')


def company_page(request, symbol):
    return render(request, 'company/detail.html', {'symbol': symbol})


@api_view(['GET'])
def company_list(request):
    sector = request.query_params.get('sector', None)
    companies = Company.objects.all().order_by('company_name')
    if sector:
        companies = companies.filter(sector=sector)
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def company_detail(request, symbol):
    try:
        company = Company.objects.get(id=symbol.upper())
    except Company.DoesNotExist:
        return Response(
            {'error': f'Company {symbol} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = CompanyDetailSerializer(company)
    return Response(serializer.data)


@api_view(['GET'])
def profit_loss(request, symbol):
    data = ProfitLoss.objects.filter(
        company_id=symbol.upper()
    ).order_by('-fiscal_year')
    serializer = ProfitLossSerializer(data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def balance_sheet(request, symbol):
    data = BalanceSheet.objects.filter(
        company_id=symbol.upper()
    ).order_by('-fiscal_year')
    serializer = BalanceSheetSerializer(data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def cash_flow(request, symbol):
    data = CashFlow.objects.filter(
        company_id=symbol.upper()
    ).order_by('-fiscal_year')
    serializer = CashFlowSerializer(data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def ml_scores(request, symbol):
    try:
        score = MLScore.objects.get(company_id=symbol.upper())
        serializer = MLScoreSerializer(score)
        return Response(serializer.data)
    except MLScore.DoesNotExist:
        return Response(
            {'error': f'Score not found for {symbol}'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def pros_cons(request, symbol):
    data = ProsCons.objects.filter(company_id=symbol.upper())
    serializer = ProsConsSerializer(data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def sector_list(request):
    sectors = Company.objects.values_list(
        'sector', flat=True
    ).distinct().order_by('sector')
    return Response(list(sectors))


@api_view(['GET'])
def top_companies(request):
    limit = int(request.query_params.get('limit', 10))
    scores = MLScore.objects.order_by('-overall_score')[:limit]
    serializer = MLScoreSerializer(scores, many=True)
    return Response(serializer.data)