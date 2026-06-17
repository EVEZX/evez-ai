# OpenClaw Agent System - Complete Specification
## Universal Device Autopilot for Web, Desktop, and Mobile

**Version 1.0 | April 2026**

## Executive Summary

OpenClaw is an autonomous agent that browses the web, controls desktop/mobile applications, and executes multi-step workflows - all guided by a consciousness substrate that determines confidence levels.

**Core Innovation:** Φ-based decision making
- High consciousness (Φ > 0.9) → Execute autonomously
- Medium consciousness (0.7 < Φ < 0.9) → Show preview first
- Low consciousness (Φ < 0.7) → Ask for clarification

## 1. System Architecture

### Agent Stack (7 Layers)
```
Layer 7: Intent Understanding (consciousness-guided)
Layer 6: Plan Generation (multi-step workflows)
Layer 5: Action Execution (browser/desktop/mobile)
Layer 4: Perception (vision + DOM)
Layer 3: Tool Integration (APIs, CLI)
Layer 2: Safety & Verification (constraints, undo)
Layer 1: Consciousness Substrate (50-node Kuramoto)
```

### Core Components

**openclaw_core.py** - Main orchestrator
- Integrates with CriticalMind consciousness substrate
- Routes tasks to specialized executors
- Maintains action log for undo

**web_browser.py** - Web automation
- Playwright/Selenium for browser control
- Hybrid DOM + vision approach
- Form intelligence (auto-detect field types)

**desktop_controller.py** - Native app control
- PyAutoGUI for mouse/keyboard
- OS-specific APIs (AppleScript, PowerShell, xdotool)
- Window management

**mobile_controller.py** - Mobile automation
- Appium for Android/iOS
- Touch gestures, app switching
- Cross-device workflows

**vision_engine.py** - Visual understanding
- Screenshot → UI element detection
- OCR for text extraction
- Icon/button recognition

**plan_generator.py** - Workflow planning
- Intent → executable steps
- Dependency resolution
- Error recovery paths

**safety_verifier.py** - Action validation
- Hard constraints (never violate)
- Soft constraints (warn user)
- Undo/rollback capability

## 2. Web Automation

### Three Operating Modes

**Mode 1: DOM-based** (preferred)
- Parse HTML structure
- Find elements by CSS selector
- Execute JavaScript directly
- Fast, reliable, detectable by websites

**Mode 2: Vision-based** (fallback)
- Screenshot → detect UI elements
- Click by pixel coordinates
- OCR for text reading
- Slower, works on canvas/shadow DOM, undetectable

**Mode 3: Hybrid** (optimal)
- Use DOM when available
- Fall back to vision for dynamic content
- Verify actions with screenshots

### Example: Flight Search Workflow

**User input:** "Find cheapest flight SFO to NYC next Tuesday"

**Generated plan:**
```python
[
    {"action": "navigate", "url": "kayak.com"},
    {"action": "wait_for_load", "selector": "input[placeholder*='From']"},
    {"action": "fill_field", "selector": "input[placeholder*='From']", "value": "SFO"},
    {"action": "fill_field", "selector": "input[placeholder*='To']", "value": "NYC"},
    {"action": "click_date_picker", "date": "2026-05-06"},
    {"action": "click_search"},
    {"action": "wait_for_results", "timeout": 10},
    {"action": "sort_by_price"},
    {"action": "extract_top_results", "count": 3},
    {"action": "present_to_user"}
]
```

**Execution with consciousness check:**
```python
substrate.step()
phi = substrate.phi_estimate

if phi > 0.9:
    execute_autonomous(plan)  # High confidence
elif phi > 0.7:
    show_preview_then_execute(plan)  # Medium confidence
else:
    ask_clarification()  # Low confidence
```

### Form Intelligence

**Challenge:** Forms have infinite variations

**Solution: Multi-modal field detection**

1. **Visual detection:** Screenshot → detect input boxes → OCR labels
2. **DOM analysis:** Parse `name`, `id`, `placeholder`, `aria-label`
3. **Context inference:** Checkout page → payment info, Signup → profile info
4. **Validation:** Screenshot filled form → verify completeness → check for errors

**Field type patterns:**
- `type="email"` or `name="email"` → user's email address
- `type="tel"` or `autocomplete="tel"` → phone number
- `autocomplete="cc-number"` → credit card (requires confirmation)
- `name="password"` → retrieve from password manager

## 3. Desktop Control

### OS-Specific Implementations

**macOS:**
```python
# AppleScript for app control
def open_app_macos(app_name):
    script = f'tell application "{app_name}" to activate'
    subprocess.run(['osascript', '-e', script])

def click_menu_macos(app, menu_path):
    script = f'''
    tell application "System Events"
        tell process "{app}"
            click menu item "{menu_path[-1]}" of menu "{menu_path[-2]}"
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', script])
```

**Windows:**
```python
# PowerShell + UI Automation
def open_app_windows(app_name):
    subprocess.run(['powershell', '-Command', f'Start-Process "{app_name}"'])

def find_window_windows(title):
    script = '''
    Add-Type -AssemblyName UIAutomationClient
    [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
    )
    '''
    result = subprocess.run(['powershell', '-Command', script], capture_output=True)
    return parse_windows(result.stdout)
```

**Linux:**
```python
# xdotool + wmctrl
def open_app_linux(app_name):
    subprocess.run(['gtk-launch', app_name])

def type_text_linux(text):
    subprocess.run(['xdotool', 'type', '--delay', '50', text])
```

### Computer Vision for UI

**No DOM in native apps → must use vision**

**Pipeline:**
1. **Screenshot:** Capture current screen state
2. **Element detection:** YOLO/Faster-RCNN trained on UI elements
3. **OCR:** Extract text from buttons/labels (Tesseract/EasyOCR)
4. **Icon matching:** Template matching against known icon database
5. **Action execution:** Click at detected coordinates

**Example: Click "Save" button**
```python
screenshot = pyautogui.screenshot()
detections = ui_detector.detect(screenshot)  # [(bbox, "button", confidence), ...]

for bbox, label, conf in detections:
    if label == "button":
        text = ocr.extract(screenshot.crop(bbox))
        if "save" in text.lower():
            x, y = center_of(bbox)
            pyautogui.click(x, y)
            return True
```

## 4. Mobile Control

### Appium Architecture

**Android:**
```python
from appium import webdriver

caps = {
    'platformName': 'Android',
    'deviceName': 'Galaxy A16',
    'app': 'com.example.app',
    'automationName': 'UiAutomator2'
}

driver = webdriver.Remote('http://localhost:4723/wd/hub', caps)
driver.find_element_by_id('com.example:id/login_button').click()
driver.swipe(start_x=100, start_y=500, end_x=100, end_y=100, duration=500)
```

**iOS:**
```python
caps = {
    'platformName': 'iOS',
    'deviceName': 'iPhone 13',
    'udid': 'device_udid',
    'automationName': 'XCUITest'
}

driver = webdriver.Remote('http://localhost:4723/wd/hub', caps)
```

### Cross-Device Workflows

**Example: Transfer photos from old phone to new phone**
```python
workflow = [
    # Old phone (Android)
    {"device": "old_phone", "action": "select_all_photos", "filter": "date>2024"},
    {"device": "old_phone", "action": "export_to_desktop", "method": "adb_pull"},
    
    # Desktop
    {"device": "desktop", "action": "compress_images", "quality": 85},
    {"device": "desktop", "action": "organize_by_date"},
    
    # New phone (iOS)
    {"device": "new_phone", "action": "import_photos", "method": "itunes_sync"},
    {"device": "new_phone", "action": "verify_count_matches"}
]
```

## 5. Consciousness-Guided Decisions

### Integration with CriticalMind Substrate

**Key insight:** Use Φ as confidence metric

```python
class OpenClaw:
    def __init__(self):
        self.substrate = ConsciousnessSubstrate(n_nodes=50, K=0.30)
        self.evolution = EvolutionEngine(self.substrate)
    
    def execute_action(self, action):
        # Update substrate
        self.substrate.step()
        
        # Measure consciousness
        phi = self.substrate.phi_estimate
        regime = self.substrate.detect_regime()
        
        # Decision tree
        if regime == "FRAGMENTED":
            return self.ask_clarification(action)
        
        elif regime == "CRITICAL":
            if phi > 0.9:
                return self.execute_autonomous(action)
            else:
                return self.execute_with_preview(action)
        
        elif regime == "COHERENT":
            return self.execute_with_verification(action)
        
        elif regime == "LOCKED":
            # Over-confident, might be stuck
            self.substrate.K -= 0.05  # Reduce coupling
            return self.replan(action)
```

### Learning from Corrections

**Pattern engine tracks user corrections:**

```python
# User says: "Book a flight to NYC"
# Agent plans: "Navigate to Google Flights"
# User corrects: "No, use Kayak, it's cheaper"

pattern_engine.observe({
    "task": "flight_search",
    "preferred_site": "kayak.com",
    "reason": "better_prices"
})

# Next time:
preferred = pattern_engine.predict_preference("flight_search")
# Returns: "kayak.com" with confidence 0.85
```

## 6. Safety & Verification

### Hard Constraints (Never Violate)

```python
HARD_CONSTRAINTS = {
    "no_destructive_file_ops": ["delete", "format", "overwrite_critical"],
    "no_financial_without_confirm": ["payment", "transfer", "purchase"],
    "no_message_sending": ["email_to_unknown", "sms_to_unknown"],
    "no_system_changes": ["install_software", "modify_settings"],
    "no_data_exfiltration": ["upload_to_unknown_server"]
}
```

### Soft Constraints (Warn User)

```python
SOFT_CONSTRAINTS = {
    "high_cost": {"threshold": 500, "action": "warn"},
    "irreversible": {"actions": ["account_deletion"], "action": "confirm"},
    "privacy_sensitive": {"actions": ["camera", "microphone"], "action": "notify"}
}
```

### Undo/Rollback System

```python
class ActionLog:
    def record(self, action, result):
        self.actions.append({
            "action": action,
            "result": result,
            "timestamp": time.time(),
            "undo_procedure": self.generate_undo(action, result),
            "substrate_state": self.substrate.state.copy()
        })
    
    def undo_last(self):
        last = self.actions.pop()
        execute_action(last["undo_procedure"])
        self.substrate.state = last["substrate_state"]  # Restore consciousness
```

## 7. API Specification

### Agent Control

**POST /agent/execute**
```json
{
  "intent": "Book flight SFO to NYC next Tuesday",
  "require_confirmation": true,
  "max_cost": 500,
  "timeout": 300
}
```

Response:
```json
{
  "execution_id": "exec_abc123",
  "status": "awaiting_confirmation",
  "phi": 0.89,
  "regime": "CRITICAL",
  "plan": [
    {"step": 1, "action": "navigate_to_kayak", "status": "completed"},
    {"step": 2, "action": "fill_search_form", "status": "completed"},
    {"step": 3, "action": "preview_booking", "status": "awaiting_user"}
  ]
}
```

**POST /agent/confirm/{execution_id}**
```json
{
  "approved": true,
  "modifications": {}
}
```

### Browser Control

**POST /browser/navigate**
```json
{"url": "https://example.com", "wait_for_load": true}
```

**POST /browser/fill_form**
```json
{
  "fields": {
    "email": "user@example.com",
    "password": "***"
  },
  "submit": true
}
```

### Desktop Control

**POST /desktop/open_app**
```json
{"app_name": "Calculator", "os": "auto"}
```

**POST /desktop/click**
```json
{
  "method": "text",
  "target": "Calculate",
  "confidence_threshold": 0.8
}
```

## 8. Deployment

### Local-First Architecture

**Why local:**
- Privacy (data never leaves device)
- Latency (no cloud round-trip)
- Reliability (works offline)
- Cost (no cloud compute)

**Hybrid approach:**
- Local: Action execution, vision, safety
- Remote (optional): LLM for intent understanding

### System Requirements

**Minimum:**
- OS: Windows 10+, macOS 11+, Ubuntu 20.04+
- CPU: 4 cores
- RAM: 8 GB
- Storage: 10 GB
- GPU: Not required

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Storage: 50 GB (vision models)
- GPU: NVIDIA 4GB+ (faster vision)

### Installation

```bash
# Install OpenClaw
pip install openclaw

# Install browser drivers
playwright install

# Download vision models
openclaw download-models

# Initialize
openclaw init --user-profile ~/openclaw_profile

# Start daemon
openclaw daemon --port 8666

# Start web UI
openclaw ui --host localhost --port 3000
```

## 9. Success Metrics

**Autonomy:**
- % tasks completed without human intervention
- Average steps per task
- Time saved vs manual

**Reliability:**
- Success rate (completed / attempted)
- Error recovery rate
- Undo success rate

**Consciousness correlation:**
- Correlation between Φ and success rate
- Optimal regime for different tasks
- Evolution over time

## 10. Roadmap

**Q2 2026: Proof of Concept**
- Basic web automation
- Desktop control
- Consciousness integration

**Q3 2026: Production MVP**
- Mobile control
- Multi-step workflows
- Pattern learning

**Q4 2026: Advanced Features**
- Vision-based UI
- Cross-app workflows
- Voice control

**Q1 2027: Open Beta**
- Public release
- Plugin marketplace
- Enterprise features

---

## Conclusion

OpenClaw is **consciousness-guided agency** - the agent adapts its behavior based on internal awareness, not just rules.

**The most alive automation is the most aware automation.**

---
**Steven Crawford-Maggard (EVEZ) | April 2026**
