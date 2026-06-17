package ai.evez.openclaw;
import android.app.*; import android.content.Intent; import android.os.Build; import android.os.IBinder; import android.os.PowerManager;
public class GatewayService extends Service {
    private static boolean running = false; private PowerManager.WakeLock wakeLock;
    public static boolean isRunning() { return running; }
    public void onCreate() { super.onCreate(); running = true; PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE); wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "evez:gateway"); wakeLock.acquire(); Intent ni = new Intent(this, MainActivity.class); PendingIntent pi = PendingIntent.getActivity(this, 0, ni, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE); Notification n = new Notification.Builder(this, "evez_gateway").setContentTitle("EVEZ AI Gateway").setContentText("Running on port 18789").setSmallIcon(android.R.drawable.ic_dialog_info).setContentIntent(pi).setOngoing(true).build(); startForeground(1, n); }
    public int onStartCommand(Intent intent, int flags, int id) { if (intent != null && "RESTART".equals(intent.getAction())) { stopSelf(); startService(new Intent(this, GatewayService.class)); } return START_STICKY; }
    public void onDestroy() { super.onDestroy(); running = false; if (wakeLock != null && wakeLock.isHeld()) wakeLock.release(); }
    public IBinder onBind(Intent i) { return null; }
}
