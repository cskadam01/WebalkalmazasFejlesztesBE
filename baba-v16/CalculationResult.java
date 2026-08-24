package hu.babatamogatas.app;

import java.util.ArrayList;
import java.util.List;

public class CalculationResult {
    public boolean csedEligible;
    public boolean gyedEligible;
    public long insuredDaysInTwoYears;
    public boolean insurance365Met;
    public boolean csedConnectionMet;
    public boolean gyedStatusMet;

    public long csedDailyBase;
    public long csedDailyAmount100;
    public long csedDailyAmount70;
    public long csedGrossMonthly;              // 30-day equivalent at 100%
    public long csedGrossMonthlyAfter90;       // 30-day equivalent at 70%
    public long csedNetMonthly;
    public long csedNetMonthlyAfter90;

    public long gyedDailyBase;
    public long gyedDailyAmountBeforeCap;
    public long gyedGrossMonthly;
    public long gyedNetMonthly;
    public long gyedNetWithContributionRelief;
    public long gyedMaximum;

    public String csedRule;
    public String gyedRule;
    public String csedStart;
    public String gyedStart;
    public String gyedEnd;
    public String calculationQuality = "";
    public boolean exactIncomeData;

    public final List<String> relationshipBreakdown = new ArrayList<>();
    public final List<String> warnings = new ArrayList<>();
    public final List<String> suggestions = new ArrayList<>();
}
