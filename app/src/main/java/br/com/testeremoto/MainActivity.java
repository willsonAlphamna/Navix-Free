package br.com.testeremoto;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.widget.*;
public class MainActivity extends Activity {
 @Override public void onCreate(Bundle b){super.onCreate(b); LinearLayout l=new LinearLayout(this);l.setOrientation(1);l.setPadding(24,36,24,24); TextView t=new TextView(this);t.setText("Samsung Remote Teste — protótipo local\n\nEste APK não espelha a tela, não rastreia localização e não transmite arquivos.\n\nUse o botão abaixo para selecionar um arquivo local.");l.addView(t);Button btn=new Button(this);btn.setText("Selecionar arquivo");btn.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,1);});l.addView(btn);setContentView(l);}
}