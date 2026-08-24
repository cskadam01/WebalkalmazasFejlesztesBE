import hu.babatamogatas.app.*;
import java.time.*;import java.util.*;
public class TestCalculator {
 private static void check(boolean x,String m){if(!x)throw new RuntimeException(m);}
 public static void main(String[] a){
  List<EmploymentPeriod> p=new ArrayList<>();
  p.add(new EmploymentPeriod("Minta Kft.", LocalDate.of(2024,1,1), null, 700000,true,0,0));
  CalculationResult r=CalculatorEngine.calculate(LocalDate.of(2027,1,27),false,p,false,false);
  check(r.csedEligible&&r.gyedEligible,"eligibility failed");
  check(r.gyedGrossMonthly==451920,"GYED max failed: "+r.gyedGrossMonthly);
  check(r.gyedNetMonthly==406728,"GYED net failed: "+r.gyedNetMonthly);
  check(r.csedRule.contains("180"),"CSED should use 180-day rule: "+r.csedRule);
  check(r.csedGrossMonthly>645600,"CSED must not be capped at 645600 under 180-day rule: "+r.csedGrossMonthly);
  List<EmploymentPeriod> q=new ArrayList<>();
  q.add(new EmploymentPeriod("Régi Kft.", LocalDate.of(2024,1,1), LocalDate.of(2026,11,30),500000,true,0,0));
  q.add(new EmploymentPeriod("Új Kft.", LocalDate.of(2026,12,5), null,900000,true,0,0));
  CalculationResult f=CalculatorEngine.calculate(LocalDate.of(2027,2,6),false,q,false,false);
  check(f.csedRule.toLowerCase().contains("fallback"),"fallback rule expected: "+f.csedRule);
  check(f.csedGrossMonthly==645600,"fallback 645600 expected, got "+f.csedGrossMonthly);
  CalculationResult w=CalculatorEngine.calculate(LocalDate.of(2027,1,27),false,p,true,false);
  check(w.csedGrossMonthly>w.csedGrossMonthlyAfter90,"70% post-90 value should be lower");
  check(Math.abs(w.csedGrossMonthlyAfter90-Math.round(w.csedGrossMonthly*0.70))<=1,"70% calculation mismatch");
  System.out.println("OK CSED180="+r.csedGrossMonthly+" CSEDfallback="+f.csedGrossMonthly+" GYED="+r.gyedGrossMonthly);
 }
}
