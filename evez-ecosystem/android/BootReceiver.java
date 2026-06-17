package ai.evez.openclaw;
import android.content.*; import android.os.Build;
public class BootReceiver extends BroadcastReceiver {
    public void onReceive(Context ctx, Intent intent) { if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) { Intent si = new Intent(ctx, GatewayService.class); if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(si); else ctx.startService(si); } }
}
