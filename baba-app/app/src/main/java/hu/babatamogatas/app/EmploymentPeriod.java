package hu.babatamogatas.app;

import java.time.LocalDate;

public class EmploymentPeriod {
    public String employer;
    public LocalDate start;
    public LocalDate end;
    public long monthlyGross;
    public boolean insured;
    public int unpaidDays;
    public int sickPayDays;

    public EmploymentPeriod(String employer, LocalDate start, LocalDate end, long monthlyGross, boolean insured, int unpaidDays, int sickPayDays) {
        this.employer = employer;
        this.start = start;
        this.end = end;
        this.monthlyGross = monthlyGross;
        this.insured = insured;
        this.unpaidDays = Math.max(0, unpaidDays);
        this.sickPayDays = Math.max(0, sickPayDays);
    }
}
