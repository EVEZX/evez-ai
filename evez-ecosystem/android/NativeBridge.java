package ai.evez.openclaw;
import android.content.Context;
import android.content.Intent;
import android.os.Vibrator;
import android.widget.Toast;
import org.json.JSONObject;
public class NativeBridge {
    private Context ctx;
    public NativeBridge(Context c) { ctx = c; }
    @android.webkit.JavascriptInterface
    public String getDeviceInfo() {
        try { JSONObject i = new JSONObject(); i.put("manufacturer", android.os.Build.MANUFACTURER); i.put("model", android.os.Build.MODEL); i.put("sdk", android.os.Build.VERSION.SDK_INT); i.put("release", android.os.Build.VERSION.RELEASE); i.put("version", "2.0.0"); return i.toString(); } catch (Exception e) { return "{}"; }
    }
    @android.webkit.JavascriptInterface
    public void showToast(String m) { Toast.makeText(ctx, m, Toast.LENGTH_SHORT).show(); }
    @android.webkit.JavascriptInterface
    public void vibrate(long ms) { try { Vibrator v = (Vibrator) ctx.getSystemService(Context.VIBRATOR_SERVICE); if (v != null) v.vibrate(ms); } catch (Exception e) {} }
    @android.webkit.JavascriptInterface
    public String getGatewayStatus() { return GatewayService.isRunning() ? "running" : "stopped"; }
    @android.webkit.JavascriptInterface
    public void restartGateway() { Intent i = new Intent(ctx, GatewayService.class); i.setAction("RESTART"); ctx.startService(i); }
}
