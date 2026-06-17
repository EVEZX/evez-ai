package com.evez.clawbreak;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.*;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * ClawBreak — Samsung Galaxy A16 WebView host
 * Fetches live endpoint from GitHub on startup; falls back to GitHub Pages PWA.
 */
public class MainActivity extends Activity {

    // Config endpoint (raw GitHub) — updated by cloud-server workflow
    private static final String ENDPOINT_JSON_URL =
        "https://raw.githubusercontent.com/EvezArt/clawbreak/main/endpoint.json";
    // Fallback if cloud server is not running
    private static final String FALLBACK_URL =
        "https://evezart.github.io/clawbreak/";

    private WebView     webView;
    private ProgressBar progressBar;
    private TextView    statusText;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler        mainHandler = new Handler(Looper.getMainLooper());

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Full-screen black background while loading
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        setContentView(root);

        // Status label
        statusText = new TextView(this);
        statusText.setText("\u26a1 EVEZ-OS connecting...");
        statusText.setTextColor(0xFF00FF41);  // matrix green
        statusText.setTextSize(14);
        statusText.setGravity(android.view.Gravity.CENTER);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.gravity = android.view.Gravity.CENTER_VERTICAL;
        lp.topMargin = -80;
        statusText.setLayoutParams(lp);
        root.addView(statusText);

        // Progress bar
        progressBar = new ProgressBar(this);
        FrameLayout.LayoutParams pbLp = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        pbLp.gravity = android.view.Gravity.CENTER;
        progressBar.setLayoutParams(pbLp);
        root.addView(progressBar);

        // WebView (hidden until URL resolved)
        webView = new WebView(this);
        webView.setVisibility(View.INVISIBLE);
        FrameLayout.LayoutParams wvLp = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
        webView.setLayoutParams(wvLp);
        root.addView(webView);

        setupWebView();
        fetchAndLoad();
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setMediaPlaybackRequiresUserGesture(false);
        ws.setCacheMode(WebSettings.LOAD_DEFAULT);
        ws.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        ws.setAllowFileAccess(true);
        ws.setUserAgentString(
            "ClawBreak/1.0 Samsung-A16 Android/14 EVEZ-OS/1.0 " + ws.getUserAgentString());

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                progressBar.setVisibility(View.GONE);
                statusText.setVisibility(View.GONE);
                webView.setVisibility(View.VISIBLE);
            }
            @Override
            public void onReceivedError(WebView view, int code, String desc, String url) {
                // If cloud server unreachable, fall back to GitHub Pages
                if (!url.equals(FALLBACK_URL)) {
                    mainHandler.post(() -> {
                        statusText.setText("Cloud server offline \u2014 loading local fallback...");
                        statusText.setVisibility(View.VISIBLE);
                        webView.loadUrl(FALLBACK_URL);
                    });
                }
            }
        });
    }

    private void fetchAndLoad() {
        executor.execute(() -> {
            String targetUrl = FALLBACK_URL;
            try {
                URL url = new URL(ENDPOINT_JSON_URL);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                conn.setRequestProperty("Cache-Control", "no-cache");

                if (conn.getResponseCode() == 200) {
                    StringBuilder sb = new StringBuilder();
                    BufferedReader reader = new BufferedReader(
                        new InputStreamReader(conn.getInputStream()));
                    String line;
                    while ((line = reader.readLine()) != null) sb.append(line);
                    reader.close();

                    JSONObject json = new JSONObject(sb.toString());
                    String cloudUrl = json.optString("url", "");
                    if (!cloudUrl.isEmpty()) {
                        targetUrl = cloudUrl;
                    }
                }
                conn.disconnect();
            } catch (Exception e) {
                // Network error — use fallback
            }

            final String finalUrl = targetUrl;
            mainHandler.post(() -> {
                statusText.setText(finalUrl.contains("ngrok") ?
                    "\u26a1 Cloud server detected…" : "\ud83d\udcf6 GitHub Pages mode");
                webView.loadUrl(finalUrl);
            });
        });
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
