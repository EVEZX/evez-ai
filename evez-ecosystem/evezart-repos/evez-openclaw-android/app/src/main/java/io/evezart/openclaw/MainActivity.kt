package io.evezart.openclaw

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.View
import android.webkit.*
import android.widget.ProgressBar
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import android.graphics.Color
import android.os.Build
import android.view.WindowManager

class MainActivity : AppCompatActivity() {

    // Endpoint fallback chain — CF Worker first, then Vercel, then HF Space, then GitHub Pages PWA
    private val ENDPOINTS = listOf(
        "https://e70b1eab-9f4a-41a1-bc0b-b3ed5a200065.vultropenclaw.com",
        "https://evezart.github.io/evez-openclaw-pwa/",
        "https://evez-openclaw-edge.evezart.workers.dev",
    )
    private var currentEndpointIdx = 0

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Samsung Galaxy A16: edge-to-edge, notch/punch-hole aware
        window.statusBarColor = Color.parseColor("#0a0a0a")
        window.navigationBarColor = Color.parseColor("#0a0a0a")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false)
        }

        setContentView(R.layout.activity_main)

        webView      = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        progressBar  = findViewById(R.id.progressBar)

        setupWebView()
        swipeRefresh.setOnRefreshListener { webView.reload() }
        swipeRefresh.setColorSchemeColors(Color.parseColor("#00ff88"))
        swipeRefresh.setProgressBackgroundColorSchemeColor(Color.parseColor("#111111"))

        webView.loadUrl(ENDPOINTS[0])
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled      = true
            domStorageEnabled      = true
            databaseEnabled        = true
            allowFileAccess        = true
            mixedContentMode       = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode              = WebSettings.LOAD_DEFAULT
            setSupportZoom(false)
            builtInZoomControls    = false
            displayZoomControls    = false
            useWideViewPort        = true
            loadWithOverviewMode   = true
            // Samsung Galaxy A16: MediaTek Helio G99, hardware acceleration OK
            setRenderPriority(WebSettings.RenderPriority.HIGH)
            mediaPlaybackRequiresUserGesture = false
            userAgentString = userAgentString.replace("Mobile", "Mobile EVEZ-OpenClaw/2.0")
        }

        WebView.setWebContentsDebuggingEnabled(false)

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                super.onReceivedError(view, request, error)
                // Fallback chain: try next endpoint
                if (currentEndpointIdx < ENDPOINTS.size - 1) {
                    currentEndpointIdx++
                    view?.loadUrl(ENDPOINTS[currentEndpointIdx])
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progressBar.progress = newProgress
                progressBar.visibility = if (newProgress < 100) View.VISIBLE else View.GONE
            }
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}