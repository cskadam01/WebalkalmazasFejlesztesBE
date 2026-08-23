package hu.babatamogatas.app;

import android.app.*;
import android.os.Bundle;
import android.content.*;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.*;
import android.widget.*;
import java.time.LocalDate;
import java.util.*;

public class MainActivity extends Activity {
    private LinearLayout root, jobsBox, resultBox;
    private EditText dueDate;
    private CheckBox earlyCsed, workAfter90, contributionRelief;
    private final List<EmploymentPeriod> jobs = new ArrayList<>();
    private final int pink = Color.rgb(184,92,122), ink=Color.rgb(70,52,60), pale=Color.rgb(255,248,250);

    @Override public void onCreate(Bundle b){ super.onCreate(b); buildUi(); }

    private void buildUi(){
        ScrollView scroll=new ScrollView(this); root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(18),dp(18),dp(18),dp(32)); root.setBackgroundColor(pale); scroll.addView(root); setContentView(scroll);
        TextView title=text("BabaEllátás 2026",30,true); title.setTextColor(pink); root.addView(title);
        root.addView(text("CSED • GYED • jogosultság • nettó/bruttó • optimalizálási ellenőrző",15,false));
        TextView note=text("Tervezési segédlet a 2026.08.23-án ellenőrzött szabályokhoz. Nem hatósági határozat; a végleges összeget a kifizetőhely/kormányhivatal állapítja meg.",12,false); note.setPadding(0,dp(8),0,dp(12)); root.addView(note);

        LinearLayout baby=card(); baby.addView(text("1. Baba és CSED kezdete",20,true));
        dueDate=input("Várható szülés (ÉÉÉÉ-HH-NN)"); dueDate.setText(LocalDate.now().plusMonths(5).toString()); baby.addView(dueDate);
        earlyCsed=check("CSED kezdete a várható szülés előtt 28 nappal", false); baby.addView(earlyCsed);
        workAfter90=check("Keresőtevékenység a gyermek 90. napja után a CSED alatt", false); baby.addView(workAfter90);
        contributionRelief=check("A GYED 10% nyugdíjjárulékára van felhasználható családi járulékkedvezmény", false); baby.addView(contributionRelief);
        root.addView(baby);

        LinearLayout jobsCard=card(); jobsCard.addView(text("2. Jogviszonyok és bérek",20,true));
        jobsCard.addView(text("Add meg az elmúlt 2+ év biztosítási jogviszonyait. A táppénzes napokat külön jelölheted, mert maga a táppénz nem ellátási alap.",13,false));
        jobsBox=new LinearLayout(this); jobsBox.setOrientation(LinearLayout.VERTICAL); jobsCard.addView(jobsBox);
        Button add=button("+ Jogviszony hozzáadása"); add.setOnClickListener(v->showJobDialog()); jobsCard.addView(add);
        Button sample=button("Mintaadat betöltése"); sample.setOnClickListener(v->loadSample()); jobsCard.addView(sample);
        root.addView(jobsCard);

        LinearLayout calcCard=card(); calcCard.addView(text("3. Kalkuláció",20,true)); Button calc=button("CSED és GYED kiszámítása"); calc.setOnClickListener(v->calculate()); calcCard.addView(calc); resultBox=new LinearLayout(this); resultBox.setOrientation(LinearLayout.VERTICAL); calcCard.addView(resultBox); root.addView(calcCard);

        LinearLayout ai=card(); ai.addView(text("4. Szerződés / igazolás elemzése",20,true));
        ai.addView(text("Biztonsági okból az APK nem tartalmaz OpenAI API-kulcsot. A fájlokat saját backendhez lehet továbbítani, amely strukturált jogviszony-adatokat ad vissza. A mostani kliensben a fájlválasztó és az integrációs pont elő van készítve.",13,false));
        Button pick=button("Dokumentum kiválasztása"); pick.setOnClickListener(v->{ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.setType("*/*"); i.addCategory(Intent.CATEGORY_OPENABLE); startActivityForResult(i,77);}); ai.addView(pick);
        root.addView(ai);

        LinearLayout law=card(); law.addView(text("5. Beépített jogi ellenőrzőlista",20,true));
        law.addView(text("• CSED: főszabály szerint 365 nap biztosítás a szülést megelőző 2 évben.\n• CSED: 168 nap; a napi alap 100%-a. 90 nap után végzett keresőtevékenységnél az érintett időszakban 70%.\n• GYED: a napi alap 70%-a, 2026-ban max. havi bruttó 451 920 Ft.\n• 180 napi tényleges jövedelem az elsődleges; ennek hiányában 120 nap + 180 nap folyamatos biztosítás; további fallback-szabályok.\n• 30 napnál hosszabb biztosítási megszakítás megtöri a folyamatosságot.\n• Táppénz/CSED/GYED/GYES nem számít GYED-alapot képező jövedelemnek.\n• CSED és GYED 2025.07.01-től SZJA-kedvezménnyel adómentes; CSED-et közteher nem terhel, GYED-et 10% nyugdíjjárulék terheli, amelyre családi járulékkedvezmény alkalmazható.\n• 2026-os családi kedvezmény adóban: 1 eltartott 20 ezer Ft, 2 eltartottnál gyermekenként 40 ezer Ft, 3+ eltartottnál gyermekenként 66 ezer Ft/hó." ,13,false)); root.addView(law);
    }

    private void showJobDialog(){
        LinearLayout x=new LinearLayout(this); x.setOrientation(LinearLayout.VERTICAL); x.setPadding(dp(16),0,dp(16),0);
        EditText emp=input("Munkáltató / jogviszony neve"); EditText start=input("Kezdet ÉÉÉÉ-HH-NN"); EditText end=input("Vége ÉÉÉÉ-HH-NN (üres = fennáll)"); EditText gross=input("Havi bruttó Ft"); gross.setInputType(2); EditText sick=input("Táppénzes napok ebben az időszakban"); sick.setInputType(2); EditText unpaid=input("Nem biztosított / fizetés nélküli napok"); unpaid.setInputType(2); CheckBox ins=check("Biztosítási jogviszony",true);
        x.addView(emp);x.addView(start);x.addView(end);x.addView(gross);x.addView(sick);x.addView(unpaid);x.addView(ins);
        new AlertDialog.Builder(this).setTitle("Jogviszony").setView(x).setPositiveButton("Mentés",(d,w)->{ try{ EmploymentPeriod p=new EmploymentPeriod(emp.getText().toString(), LocalDate.parse(start.getText().toString()), end.getText().toString().trim().isEmpty()?null:LocalDate.parse(end.getText().toString()), Long.parseLong(gross.getText().toString()), ins.isChecked(), parseInt(unpaid), parseInt(sick)); jobs.add(p); renderJobs(); }catch(Exception e){ toast("Hibás dátum vagy összeg. Példa dátum: 2026-08-23"); }}).setNegativeButton("Mégse",null).show();
    }

    private int parseInt(EditText e){ try{return Integer.parseInt(e.getText().toString());}catch(Exception x){return 0;} }
    private void loadSample(){ jobs.clear(); jobs.add(new EmploymentPeriod("Minta Kft.",LocalDate.now().minusYears(2),null,650000,true,0,20)); renderJobs(); }
    private void renderJobs(){ jobsBox.removeAllViews(); int i=1; for(EmploymentPeriod p:jobs){ TextView t=text(i+". "+p.employer+"\n"+p.start+" – "+(p.end==null?"fennáll":p.end)+"  •  "+money(p.monthlyGross)+" bruttó/hó  •  táppénz: "+p.sickPayDays+" nap",13,false); t.setPadding(dp(8),dp(8),dp(8),dp(8)); jobsBox.addView(t); i++; } }

    private void calculate(){ resultBox.removeAllViews(); try{
        LocalDate due=LocalDate.parse(dueDate.getText().toString()); CalculationResult r=CalculatorEngine.calculate(due,earlyCsed.isChecked(),jobs,workAfter90.isChecked(),contributionRelief.isChecked());
        resultBox.addView(text("Jogosultsági becslés",18,true));
        resultBox.addView(text("CSED: "+(r.csedEligible?"valószínűleg jogosult":"nem igazolható")+"\nGYED: "+(r.gyedEligible?"valószínűleg jogosult":"nem igazolható")+"\nBiztosított napok a szülést megelőző 2 évben: "+r.insuredDaysInTwoYears,14,false));
        resultBox.addView(text("CSED",18,true)); resultBox.addView(text("Kezdet: "+r.csedStart+"\nSzámítás: "+r.csedRule+"\nHavi bruttó becslés: "+money(r.csedGrossMonthly)+"\nHavi nettó becslés: "+money(r.csedNetMonthly),14,false));
        resultBox.addView(text("GYED",18,true)); resultBox.addView(text("Várható kezdet: "+r.gyedStart+"\nVárható vége: "+r.gyedEnd+"\nSzámítás: "+r.gyedRule+"\n2026 plafon: "+money(r.gyedMaximum)+"\nHavi bruttó becslés: "+money(r.gyedGrossMonthly)+"\nHavi nettó (10% nyugdíjjárulék): "+money(r.gyedNetMonthly)+"\nNettó, ha a családi járulékkedvezmény teljesen lefedi a 10%-ot: "+money(r.gyedNetWithContributionRelief),14,false));
        if(!r.suggestions.isEmpty()){ resultBox.addView(text("Javaslatok",18,true)); for(String s:r.suggestions) resultBox.addView(text("• "+s,13,false)); }
        if(!r.warnings.isEmpty()){ resultBox.addView(text("Ellenőrizendő",18,true)); for(String s:r.warnings) resultBox.addView(text("• "+s,13,false)); }
    }catch(Exception e){toast("Add meg a várható szülés dátumát és legalább egy jogviszonyt.");}}

    @Override protected void onActivityResult(int req,int res,Intent data){ super.onActivityResult(req,res,data); if(req==77&&res==RESULT_OK&&data!=null){ Uri u=data.getData(); toast("Dokumentum kiválasztva. A backend-integrációhoz: "+(u==null?"ismeretlen":u.getLastPathSegment())); }}

    private LinearLayout card(){ LinearLayout c=new LinearLayout(this); c.setOrientation(LinearLayout.VERTICAL); c.setPadding(dp(16),dp(16),dp(16),dp(16)); c.setBackgroundResource(hu.babatamogatas.app.R.drawable.card_bg); LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2); lp.setMargins(0,dp(10),0,dp(10)); c.setLayoutParams(lp); return c; }
    private TextView text(String s,int sp,boolean bold){ TextView t=new TextView(this); t.setText(s); t.setTextSize(sp); t.setTextColor(ink); if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD); t.setPadding(0,dp(5),0,dp(5)); return t; }
    private EditText input(String hint){ EditText e=new EditText(this); e.setHint(hint); e.setTextColor(ink); e.setHintTextColor(Color.rgb(145,125,133)); e.setSingleLine(true); return e; }
    private CheckBox check(String s,boolean checked){CheckBox c=new CheckBox(this);c.setText(s);c.setChecked(checked);c.setTextColor(ink);return c;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setBackgroundResource(R.drawable.button_bg); LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(8),0,dp(4));b.setLayoutParams(lp);return b;}
    private int dp(int x){return (int)(x*getResources().getDisplayMetrics().density+.5f);} private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();} private String money(long v){return String.format(Locale.forLanguageTag("hu-HU"),"%,d Ft",v).replace(',', ' ');} 
}
