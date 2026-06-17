package com.evez.openclaw;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.*;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.app.AlertDialog;
import android.app.ProgressDialog;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.InputStream;

public class MainActivity extends Activity {

    private WebView webView;
    private String gatewayUrl;
    private Process gatewayProcess;
    private static final String PREFS = "openclaw_prefs";
    private static final String KEY_URL = "gateway_url";
    private static final String KEY_INITIALIZED = "gateway_initialized";
    private static final String DEFAULT_URL = "http://127.0.0.1:18789";

    // Paths inside the app's private directory
    private String homeDir;
    private String nodeDir;
    private String openclawDir;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );

        // Set up paths
        homeDir = getFilesDir().getAbsolutePath() + "/home";
        nodeDir = getFilesDir().getAbsolutePath() + "/node";
        openclawDir = homeDir + "/.openclaw";

        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        gatewayUrl = prefs.getString(KEY_URL, DEFAULT_URL);

        // Create directories
        new File(homeDir).mkdirs();
        new File(openclawDir).mkdirs();
        new File(openclawDir + "/workspace").mkdirs();

        // Start the foreground service to keep us alive
        Intent serviceIntent = new Intent(this, OpenClawService.class);
        startForegroundService(serviceIntent);

        // Check if gateway is initialized, if not bootstrap it
        boolean initialized = prefs.getBoolean(KEY_INITIALIZED, false);

        // Set up WebView first
        webView = new WebView(this);
        setupWebView();
        setContentView(webView);

        // Start gateway
        if (initialized) {
            startGateway();
        } else {
            showBootstrapDialog();
        }
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " EVEZOpenClaw/2.0-Native");
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError error) {
                if (request.isForMainFrame()) {
                    // Gateway not ready yet — show loading state
                    webView.loadDataWithBaseURL(null,
                        "<html><body style='background:#0a0a0f;color:#e0e0e0;" +
                        "display:flex;justify-content:center;align-items:center;" +
                        "height:100vh;font-family:sans-serif;text-align:center;'>" +
                        "<div><h1 style='color:#ff4500'>🌀</h1>" +
                        "<p>Starting gateway...</p>" +
                        "<p style='color:#666;font-size:0.8em'>If this persists, check settings</p></div></body></html>",
                        "text/html", "UTF-8", null);
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                // Allow local and configured gateway URLs
                if (url.startsWith("http://localhost") || url.startsWith("http://127.0.0.1") ||
                    url.startsWith("http://192.168") || url.startsWith("http://10.") ||
                    url.contains("openclaw") || url.startsWith("https://")) {
                    return false;
                }
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                request.grant(request.getResources());
            }
        });

        // Native bridge
        webView.addJavascriptInterface(new Object() {
            @android.webkit.JavascriptInterface
            public void setGatewayUrl(String url) {
                SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
                prefs.edit().putString(KEY_URL, url).apply();
                gatewayUrl = url;
                runOnUiThread(() -> loadGateway());
            }

            @android.webkit.JavascriptInterface
            public String getGatewayUrl() {
                return gatewayUrl;
            }

            @android.webkit.JavascriptInterface
            public void showSettings() {
                runOnUiThread(() -> showConnectionDialog());
            }

            @android.webkit.JavascriptInterface
            public String getGatewayStatus() {
                if (gatewayProcess != null && gatewayProcess.isAlive()) {
                    return "running";
                }
                return "stopped";
            }

            @android.webkit.JavascriptInterface
            public void restartGateway() {
                stopGateway();
                new Handler(Looper.getMainLooper()).postDelayed(() -> {
                    startGateway();
                    loadGateway();
                }, 2000);
            }

            @android.webkit.JavascriptInterface
            public String execCommand(String cmd) {
                return executeShellCommand(cmd);
            }
        }, "EVEZBridge");
    }

    private void startGateway() {
        new Thread(() -> {
            try {
                // Check if node/openclaw is available in the app's private dir
                File nodeBin = new File(nodeDir + "/bin/node");
                File openclawBin = new File(nodeDir + "/bin/openclaw");

                // If bundled Node exists, use it; otherwise try system
                String nodePath;
                String openclawPath;

                if (nodeBin.exists()) {
                    nodePath = nodeBin.getAbsolutePath();
                } else {
                    // Fallback: try system node (for Termux-installed scenarios)
                    nodePath = "node";
                }

                if (openclawBin.exists()) {
                    openclawPath = openclawBin.getAbsolutePath();
                } else {
                    openclawPath = "openclaw";
                }

                // Build the gateway command
                ProcessBuilder pb;
                String port = gatewayUrl.replaceAll(".*:", "").replaceAll("[^0-9]", "");
                if (port.isEmpty()) port = "18789";

                // Try running openclaw gateway directly
                pb = new ProcessBuilder(openclawPath, "gateway",
                    "--port", port,
                    "--allow-unconfigured");

                // Set up environment
                pb.environment().put("HOME", homeDir);
                pb.environment().put("OPENCLAW_HOME", openclawDir);
                pb.environment().put("OPENCLAW_CONFIG_PATH", openclawDir + "/openclaw.json");
                pb.environment().put("OPENCLAW_WORKSPACE_DIR", openclawDir + "/workspace");
                pb.environment().put("OPENCLAW_STATE_DIR", openclawDir + "/state");
                pb.environment().put("PATH", nodeDir + "/bin:" + System.getenv("PATH"));
                pb.environment().put("NODE_ENV", "production");

                new File(openclawDir + "/state").mkdirs();

                pb.redirectErrorStream(true);
                pb.directory(new File(homeDir));

                gatewayProcess = pb.start();

                // Read output in background
                BufferedReader reader = new BufferedReader(
                    new InputStreamReader(gatewayProcess.getInputStream()));
                String line;
                while ((line = reader.readLine()) != null) {
                    // Could log this or send to WebView
                }
            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() ->
                    Toast.makeText(this, "Gateway error: " + e.getMessage(),
                        Toast.LENGTH_LONG).show()
                );
            }
        }).start();

        // Wait a moment then load the WebView
        new Handler(Looper.getMainLooper()).postDelayed(this::loadGateway, 3000);
    }

    private void stopGateway() {
        if (gatewayProcess != null && gatewayProcess.isAlive()) {
            gatewayProcess.destroy();
            gatewayProcess = null;
        }
    }

    private String executeShellCommand(String cmd) {
        try {
            ProcessBuilder pb = new ProcessBuilder("sh", "-c", cmd);
            pb.environment().put("HOME", homeDir);
            pb.environment().put("PATH", nodeDir + "/bin:" + System.getenv("PATH"));
            pb.redirectErrorStream(true);
            Process p = pb.start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
            p.waitFor();
            return output.toString();
        } catch (Exception e) {
            return "Error: " + e.getMessage();
        }
    }

    private void loadGateway() {
        webView.loadUrl(gatewayUrl);
    }

    private void showBootstrapDialog() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        TextView info = new TextView(this);
        info.setText("First run: EVEZ OpenClaw will set up on this device.\n\n" +
            "Option 1: Install via Termux (recommended)\n" +
            "  • Install Termux from F-Droid\n" +
            "  • Run the bootstrap script\n" +
            "  • Gateway runs locally on your phone\n\n" +
            "Option 2: Connect to remote gateway\n" +
            "  • Enter URL of a gateway running elsewhere\n\n" +
            "The gateway URL can be changed anytime in Settings.");
        info.setTextSize(14);
        layout.addView(info);

        new AlertDialog.Builder(this)
            .setTitle("🌀 EVEZ OpenClaw Setup")
            .setView(layout)
            .setPositiveButton("Termux Bootstrap", (dialog, which) -> {
                // Open Termux install page
                Intent intent = new Intent(Intent.ACTION_VIEW,
                    Uri.parse("https://f-droid.org/en/packages/com.termux/"));
                startActivity(intent);

                // Also copy bootstrap command
                String bootstrapCmd = "curl -fsSL https://raw.githubusercontent.com/EvezArt/evez-openclaw-deploy/main/scripts/a16-termux-bootstrap.sh | bash";
                android.content.ClipboardManager clipboard = (android.content.ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(android.content.ClipData.newPlainText("bootstrap", bootstrapCmd));

                Toast.makeText(this, "Bootstrap command copied to clipboard!\nPaste it in Termux.", Toast.LENGTH_LONG).show();

                SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
                prefs.edit().putBoolean(KEY_INITIALIZED, true).apply();
                loadGateway();
            })
            .setNeutralButton("Remote Gateway", (dialog, which) -> {
                showConnectionDialog();
            })
            .setCancelable(false)
            .show();
    }

    private void showConnectionDialog() {
        runOnUiThread(() -> {
            LinearLayout layout = new LinearLayout(this);
            layout.setOrientation(LinearLayout.VERTICAL);
            layout.setPadding(50, 40, 50, 10);

            EditText input = new EditText(this);
            input.setHint("Gateway URL (e.g. http://127.0.0.1:18789)");
            input.setText(gatewayUrl);
            input.setSelectAllOnFocus(true);
            layout.addView(input);

            TextView status = new TextView(this);
            status.setText("\nGateway: " + (gatewayProcess != null && gatewayProcess.isAlive() ? "● Running" : "○ Stopped"));
            status.setTextSize(12);
            layout.addView(status);

            new AlertDialog.Builder(this)
                .setTitle("EVEZ OpenClaw Gateway")
                .setMessage("Local: http://127.0.0.1:18789\nLAN: http://YOUR_IP:18789\nCloud: https://your-deploy.fly.dev")
                .setView(layout)
                .setPositiveButton("Connect", (dialog, which) -> {
                    String url = input.getText().toString().trim();
                    if (!url.isEmpty()) {
                        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
                        prefs.edit().putString(KEY_URL, url).apply();
                        gatewayUrl = url;
                        loadGateway();
                    }
                })
                .setNeutralButton("Start Local", (dialog, which) -> {
                    startGateway();
                })
                .setCancelable(false)
                .show();
        });
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            showConnectionDialog();
        }
    }

    @Override
    protected void onDestroy() {
        stopGateway();
        stopService(new Intent(this, OpenClawService.class));
        super.onDestroy();
    }
}
