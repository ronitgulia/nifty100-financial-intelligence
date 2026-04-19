from django.db import models


class Company(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100)
    company_logo = models.TextField(null=True)
    about_company = models.TextField(null=True)
    website = models.CharField(max_length=200, null=True)
    nse_profile = models.CharField(max_length=200, null=True)
    bse_profile = models.CharField(max_length=200, null=True)
    face_value = models.FloatField(null=True)
    book_value = models.FloatField(null=True)
    roce_percentage = models.FloatField(null=True)
    roe_percentage = models.FloatField(null=True)

    class Meta:
        db_table = 'dim_company'
        managed = False

    def __str__(self):
        return self.company_name


class ProfitLoss(models.Model):
    company_id = models.CharField(max_length=20)
    year = models.CharField(max_length=20)
    sales = models.FloatField(null=True)
    expenses = models.FloatField(null=True)
    operating_profit = models.FloatField(null=True)
    opm_percentage = models.FloatField(null=True)
    net_profit = models.FloatField(null=True)
    eps = models.FloatField(null=True)
    net_profit_margin_pct = models.FloatField(null=True)
    fiscal_year = models.FloatField(null=True)

    class Meta:
        db_table = 'fact_profit_loss'
        managed = False

    def __str__(self):
        return f"{self.company_id} - {self.year}"


class BalanceSheet(models.Model):
    company_id = models.CharField(max_length=20)
    year = models.CharField(max_length=20)
    equity_capital = models.FloatField(null=True)
    reserves = models.FloatField(null=True)
    borrowings = models.FloatField(null=True)
    total_assets = models.FloatField(null=True)
    total_liabilities = models.FloatField(null=True)
    debt_to_equity = models.FloatField(null=True)
    fiscal_year = models.FloatField(null=True)

    class Meta:
        db_table = 'fact_balance_sheet'
        managed = False

    def __str__(self):
        return f"{self.company_id} - {self.year}"


class CashFlow(models.Model):
    company_id = models.CharField(max_length=20)
    year = models.CharField(max_length=20)
    operating_activity = models.FloatField(null=True)
    investing_activity = models.FloatField(null=True)
    financing_activity = models.FloatField(null=True)
    net_cash_flow = models.FloatField(null=True)
    free_cash_flow = models.FloatField(null=True)
    fiscal_year = models.FloatField(null=True)

    class Meta:
        db_table = 'fact_cash_flow'
        managed = False

    def __str__(self):
        return f"{self.company_id} - {self.year}"


class MLScore(models.Model):
    company_id = models.CharField(max_length=20, primary_key=True)
    overall_score = models.FloatField(null=True)
    profitability_score = models.FloatField(null=True)
    leverage_score = models.FloatField(null=True)
    cashflow_score = models.FloatField(null=True)
    growth_score = models.FloatField(null=True)
    health_label = models.CharField(max_length=20, null=True)

    class Meta:
        db_table = 'fact_ml_scores'
        managed = False

    def __str__(self):
        return f"{self.company_id} - {self.health_label}"


class ProsCons(models.Model):
    company_id = models.CharField(max_length=20, primary_key=True)  # yeh badlo
    is_pro = models.BooleanField(null=True)
    text = models.TextField(null=True)

    class Meta:
        db_table = 'fact_pros_cons'
        managed = False

    def __str__(self):
        return f"{self.company_id} - {'Pro' if self.is_pro else 'Con'}"