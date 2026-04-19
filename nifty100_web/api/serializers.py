from rest_framework import serializers
from .models import Company, ProfitLoss, BalanceSheet, CashFlow, MLScore, ProsCons


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class ProfitLossSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitLoss
        fields = '__all__'


class BalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceSheet
        fields = '__all__'


class CashFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashFlow
        fields = '__all__'


class MLScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLScore
        fields = '__all__'


class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProsCons
        fields = '__all__'


class CompanyDetailSerializer(serializers.ModelSerializer):
    health_label = serializers.SerializerMethodField()
    overall_score = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'company_name', 'sector',
            'company_logo', 'about_company',
            'website', 'nse_profile', 'bse_profile',
            'face_value', 'book_value',
            'roce_percentage', 'roe_percentage',
            'health_label', 'overall_score'
        ]

    def get_health_label(self, obj):
        score = MLScore.objects.filter(company_id=obj.id).first()
        return score.health_label if score else None

    def get_overall_score(self, obj):
        score = MLScore.objects.filter(company_id=obj.id).first()
        return score.overall_score if score else None