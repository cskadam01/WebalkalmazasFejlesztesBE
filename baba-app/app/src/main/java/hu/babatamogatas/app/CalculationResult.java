package hu.babatamogatas.app;

import java.util.ArrayList;
import java.util.List;

public class CalculationResult {
    public boolean csedEligible;
    public boolean gyedEligible;
    public long insuredDaysInTwoYears;
    public long csedGrossMonthly;
    public long csedNetMonthly;
    public long gyedGrossMonthly;
    public long gyedNetMonthly;
    public long gyedNetWithContributionRelief;
    public long gyedMaximum;
    public String csedRule;
    public String gyedRule;
    public String csedStart;
    public String gyedStart;
    public String gyedEnd;
    public final List<String> warnings = new ArrayList<>();
    public final List<String> suggestions = new ArrayList<>();
}
