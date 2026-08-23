package hu.babatamogatas.app;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * 2026 forecasting engine based on the rules published by the Hungarian State Treasury.
 * This is a planning calculator, not an authority decision. It intentionally exposes the rule used.
 */
public final class CalculatorEngine {
    public static final long MIN_WAGE_2026 = 322_800L;
    public static final long GUARANTEED_MIN_2026 = 373_200L;
    public static final long GYED_MAX_2026 = 451_920L;

    private CalculatorEngine() {}

    public static CalculationResult calculate(LocalDate expectedBirth, boolean csedFrom28DaysBefore,
                                              List<EmploymentPeriod> periods, boolean workAfterCsedDay90,
                                              boolean applyFamilyContributionRelief) {
        CalculationResult r = new CalculationResult();
        LocalDate birth = expectedBirth;
        LocalDate csedStart = csedFrom28DaysBefore ? birth.minusDays(28) : birth;
        LocalDate gyedStart = csedStart.plusDays(168);
        LocalDate gyedEnd = birth.plusYears(2).minusDays(1);
        r.csedStart = csedStart.toString();
        r.gyedStart = gyedStart.toString();
        r.gyedEnd = gyedEnd.toString();
        r.gyedMaximum = GYED_MAX_2026;

        r.insuredDaysInTwoYears = insuredDays(periods, birth.minusYears(2), birth.minusDays(1));
        r.csedEligible = r.insuredDaysInTwoYears >= 365 && hasCsedBirthConnection(periods, birth);
        r.gyedEligible = r.insuredDaysInTwoYears >= 365 && isInsuredAround(periods, gyedStart);

        if (!r.csedEligible) r.warnings.add("A megadott adatok alapján a CSED általános jogosultsági feltétele nem igazolható (365 nap és a szüléskori/passzív feltétel ellenőrzendő). Méltányosság külön vizsgálandó.");
        if (!r.gyedEligible) r.warnings.add("A megadott adatok alapján a GYED általános jogosultsága nem biztos. A 365 napos előzetes biztosítást és a GYED kezdetekor fennálló jogállást hatósági adatokkal is ellenőrizni kell.");

        Base csedBase = determineBase(csedStart, periods, true);
        Base gyedBase = determineBase(gyedStart, periods, false);
        double csedRate = workAfterCsedDay90 ? 0.70 : 1.00;
        r.csedGrossMonthly = roundFt(csedBase.daily * 30.0 * csedRate);
        r.csedNetMonthly = r.csedGrossMonthly;
        long gyedUncapped = roundFt(gyedBase.daily * 30.0 * 0.70);
        r.gyedGrossMonthly = Math.min(gyedUncapped, GYED_MAX_2026);
        r.gyedNetMonthly = roundFt(r.gyedGrossMonthly * 0.90);
        r.gyedNetWithContributionRelief = applyFamilyContributionRelief ? r.gyedGrossMonthly : r.gyedNetMonthly;
        r.csedRule = csedBase.rule;
        r.gyedRule = gyedBase.rule + (gyedUncapped > GYED_MAX_2026 ? "; a 2026-os GYED plafon alkalmazva" : "");

        if (gyedUncapped >= GYED_MAX_2026) {
            r.suggestions.add("A jelenlegi adatokkal a GYED eléri a 2026-os maximumot; további béremelés önmagában a GYED havi bruttó összegét már nem növeli.");
        } else {
            long targetMonthlyBase = (long)Math.ceil(GYED_MAX_2026 / 0.70);
            r.suggestions.add("A GYED-maximalizálás elméleti havi alapja kb. " + targetMonthlyBase + " Ft. Csak valós munkaviszonyból, ténylegesen járulékalapot képező jövedelem tervezhető; mesterséges vagy utólagos bérkonstrukciót az app nem javasol.");
        }
        r.suggestions.add("A CSED kezdőnapja legkorábban a várható szülés előtti 28. nap lehet; a választott kezdőnap a figyelembe vehető jövedelmi időszakot is módosíthatja.");
        r.suggestions.add("Táppénz, CSED, GYED és GYES összege nem képez GYED-alapot; a táppénzes napok mellett a biztosítás fennállhat, de a jövedelmi napok száma csökkenhet.");
        r.suggestions.add("Ha korábbi, már megszűnt biztosítási jogviszony jövedelmének beszámítása magasabb CSED-et eredményezne, a végleges döntést követő 30 napon belül külön kérelemnek lehet jelentősége.");
        if (workAfterCsedDay90) r.warnings.add("A program azt feltételezi, hogy a gyermek születésétől számított 90. nap után keresőtevékenység történik, ezért a CSED-et 70%-os mértékkel mutatja arra az időszakra.");
        r.warnings.add("A nettó GYED alapnézetben 10% nyugdíjjárulékkal számol. A családi járulékkedvezmény a nyilatkozattól és a családi kedvezmény felhasználásától függően ezt részben vagy egészben csökkentheti.");
        return r;
    }

    private static Base determineBase(LocalDate entitlementStart, List<EmploymentPeriod> periods, boolean csed) {
        EmploymentPeriod current = currentRelationship(periods, entitlementStart);
        if (current == null) return new Base((MIN_WAGE_2026 * 2.0) / 30.0, "Nincs azonosítható fennálló jogviszony: óvatos, minimálbér kétszeresén alapuló becslés");

        LocalDate cutoff = entitlementStart.minusMonths(3).withDayOfMonth(1).minusDays(1);
        LocalDate floor = entitlementStart.minusYears(1).withDayOfYear(1);
        LocalDate continuityStart = continuousStart(periods, current, entitlementStart);
        LocalDate searchStart = floor.isAfter(continuityStart) ? floor : continuityStart;

        List<DayIncome> incomeDays = new ArrayList<>();
        for (EmploymentPeriod p : periods) {
            if (!sameRelationship(p, current) || !p.insured) continue;
            LocalDate s = max(p.start, searchStart);
            LocalDate e = min(p.end == null ? cutoff : p.end, cutoff);
            if (e.isBefore(s)) continue;
            long days = ChronoUnit.DAYS.between(s, e) + 1;
            int excluded = Math.min((int)days, p.sickPayDays + p.unpaidDays);
            long count = Math.max(0, days - excluded);
            double daily = p.monthlyGross / 30.0;
            for (int i=0; i<count; i++) incomeDays.add(new DayIncome(daily));
        }
        Collections.reverse(incomeDays);
        if (incomeDays.size() >= 180) return new Base(avg(incomeDays,180), "180 naptári napi tényleges jövedelem");
        long continuous = ChronoUnit.DAYS.between(continuityStart, entitlementStart) + 1;
        if (incomeDays.size() >= 120 && continuous >= 180) return new Base(avg(incomeDays,120), "120 naptári napi tényleges jövedelem + legalább 180 nap folyamatos biztosítás");
        if (!csed && continuous >= 180 && incomeDays.size() >= 30) return new Base(avg(incomeDays, Math.min(30,incomeDays.size())), "legalább 30 napi tényleges jövedelem + legalább 180 nap folyamatos biztosítás");

        double contractDaily = current.monthlyGross / 30.0;
        double cap = (MIN_WAGE_2026 * 2.0) / 30.0;
        return new Base(Math.min(contractDaily, cap), "tényleges/szerződés szerinti jövedelem, legfeljebb a minimálbér kétszerese");
    }

    private static long insuredDays(List<EmploymentPeriod> periods, LocalDate from, LocalDate to) {
        Set<LocalDate> set = new HashSet<>();
        for (EmploymentPeriod p : periods) {
            if (!p.insured) continue;
            LocalDate s = max(p.start, from);
            LocalDate e = min(p.end == null ? to : p.end, to);
            if (e.isBefore(s)) continue;
            for (LocalDate d=s; !d.isAfter(e); d=d.plusDays(1)) set.add(d);
        }
        return set.size();
    }

    private static boolean hasCsedBirthConnection(List<EmploymentPeriod> periods, LocalDate birth) {
        for (EmploymentPeriod p : periods) {
            if (!p.insured) continue;
            LocalDate end = p.end == null ? birth.plusYears(10) : p.end;
            if (!birth.isBefore(p.start) && !birth.isAfter(end.plusDays(42))) return true;
        }
        return false;
    }

    private static boolean isInsuredAround(List<EmploymentPeriod> periods, LocalDate date) {
        for (EmploymentPeriod p : periods) {
            if (!p.insured) continue;
            LocalDate end = p.end == null ? date.plusDays(1) : p.end;
            if (!date.isBefore(p.start) && !date.isAfter(end)) return true;
        }
        return false;
    }

    private static EmploymentPeriod currentRelationship(List<EmploymentPeriod> periods, LocalDate date) {
        EmploymentPeriod best = null;
        for (EmploymentPeriod p : periods) {
            LocalDate end = p.end == null ? date.plusYears(5) : p.end;
            if (!date.isBefore(p.start) && !date.isAfter(end)) if (best == null || p.start.isAfter(best.start)) best=p;
        }
        if (best == null) for (EmploymentPeriod p:periods) if (best==null || p.start.isAfter(best.start)) best=p;
        return best;
    }

    private static LocalDate continuousStart(List<EmploymentPeriod> all, EmploymentPeriod current, LocalDate entitlement) {
        List<EmploymentPeriod> ps = new ArrayList<>();
        for (EmploymentPeriod p:all) if (p.insured && sameRelationship(p,current)) ps.add(p);
        ps.sort(Comparator.comparing(a->a.start));
        LocalDate start = current.start;
        LocalDate lastStart = current.start;
        for (int i=ps.size()-1;i>=0;i--) {
            EmploymentPeriod p=ps.get(i);
            if (p.start.isAfter(lastStart)) continue;
            LocalDate pend=p.end==null?entitlement:p.end;
            long gap=ChronoUnit.DAYS.between(pend, start)-1;
            if (gap<=30) { start=p.start; lastStart=p.start; } else break;
        }
        return start;
    }

    private static boolean sameRelationship(EmploymentPeriod a, EmploymentPeriod b) {
        return a.employer != null && b.employer != null && a.employer.trim().equalsIgnoreCase(b.employer.trim());
    }
    private static LocalDate max(LocalDate a, LocalDate b){ return a.isAfter(b)?a:b; }
    private static LocalDate min(LocalDate a, LocalDate b){ return a.isBefore(b)?a:b; }
    private static double avg(List<DayIncome> days, int n){ double s=0; for(int i=0;i<n;i++) s+=days.get(i).v; return s/n; }
    private static long roundFt(double v){ return Math.round(v); }
    private static final class DayIncome { final double v; DayIncome(double v){this.v=v;} }
    private static final class Base { final double daily; final String rule; Base(double daily,String rule){this.daily=daily;this.rule=rule;} }
}
