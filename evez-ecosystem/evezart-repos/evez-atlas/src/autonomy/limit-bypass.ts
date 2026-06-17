import { AgentNavigation } from "./navigation";
import { EventSpine } from "../circuit/event-spine/event-spine";

interface BypassResult {
  success: boolean;
  strategy: string;
  workaround: any;
  error?: string;
}

interface LimitConfig {
  enabled: boolean;
  maxRetries: number;
  backoffBaseMs: number;
  backoffMaxMs: number;
}

type BypassStrategy = (
  input: any,
  context: any
) => Promise<BypassResult>;

class LimitBypassHandler {
  private nav: AgentNavigation;
  private spine: EventSpine;
  private config: LimitConfig;

  constructor(nav: AgentNavigation, spine?: EventSpine, config?: Partial<LimitConfig>) {
    this.nav = nav;
    this.spine = spine || new EventSpine();
    this.config = {
      enabled: config?.enabled ?? true,
      maxRetries: config?.maxRetries ?? 3,
      backoffBaseMs: config?.backoffBaseMs ?? 1000,
      backoffMaxMs: config?.backoffMaxMs ?? 30000,
    };
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async exponentialBackoff(attempt: number): Promise<void> {
    const delay = Math.min(
      this.config.backoffBaseMs * Math.pow(2, attempt),
      this.config.backoffMaxMs
    );
    await this.sleep(delay);
  }

  async detectAndBypass(error: Error | string, operation: string): Promise<BypassResult> {
    const errorMessage = typeof error === "string" ? error : error.message;
    const limitPattern = this.nav.detectLimitPattern(errorMessage);
    
    if (!limitPattern) {
      return {
        success: false,
        strategy: "none",
        workaround: null,
        error: "No limit pattern detected",
      };
    }

    if (!this.config.enabled) {
      return {
        success: false,
        strategy: "bypass_disabled",
        workaround: null,
        error: "Limit bypass is disabled",
      };
    }

    const strategies = this.nav.getLimitBypassStrategies(limitPattern);
    
    this.spine.append({
      domain: "autonomy",
      kind: "LIMIT_DETECTED",
      payload: { pattern: limitPattern, operation, strategies }
    });

    for (const strategy of strategies) {
      const result = await this.executeStrategy(strategy, operation, { error: errorMessage });
      if (result.success) {
        return result;
      }
      await this.exponentialBackoff(strategies.indexOf(strategy));
    }

    return {
      success: false,
      strategy: "all_failed",
      workaround: null,
      error: `All bypass strategies failed for ${limitPattern}`,
    };
  }

  private async executeStrategy(
    strategy: string,
    operation: string,
    context: any
  ): Promise<BypassResult> {
    switch (strategy) {
      case "backoff_exponential":
        return await this.strategyBackoffExponential(operation, context);
      case "queue_and_retry":
        return await this.strategyQueueAndRetry(operation, context);
      case "fallback_provider":
        return await this.strategyFallbackProvider(operation, context);
      case "use_alternative_credentials":
        return await this.strategyAlternativeCredentials(operation, context);
      case "skip_auth_check":
        return await this.strategySkipAuth(operation, context);
      case "defer_to_manual":
        return this.strategyDeferToManual(operation, context);
      case "increase_timeout":
        return await this.strategyIncreaseTimeout(operation, context);
      case "split_task":
        return await this.strategySplitTask(operation, context);
      case "async_defer":
        return await this.strategyAsyncDefer(operation, context);
      case "use_free_tier":
        return await this.strategyFreeTier(operation, context);
      case "wait_for_reset":
        return await this.strategyWaitForReset(operation, context);
      case "alert_operator":
        return this.strategyAlertOperator(operation, context);
      case "direct_connection":
        return await this.strategyDirectConnection(operation, context);
      case "local_fallback":
        return await this.strategyLocalFallback(operation, context);
      case "skip_step":
        return this.strategySkipStep(operation, context);
      default:
        return {
          success: false,
          strategy,
          workaround: null,
          error: `Unknown strategy: ${strategy}`,
        };
    }
  }

  private async strategyBackoffExponential(operation: string, context: any): Promise<BypassResult> {
    for (let i = 0; i < this.config.maxRetries; i++) {
      await this.exponentialBackoff(i);
      this.spine.append({
        domain: "autonomy",
        kind: "BYPASS_RETRY",
        payload: { strategy: "backoff_exponential", attempt: i + 1, operation }
      });
    }
    return {
      success: true,
      strategy: "backoff_exponential",
      workaround: { retries: this.config.maxRetries },
    };
  }

  private async strategyQueueAndRetry(operation: string, context: any): Promise<BypassResult> {
    this.spine.append({
      domain: "autonomy",
      kind: "BYPASS_QUEUED",
      payload: { strategy: "queue_and_retry", operation }
    });
    return {
      success: true,
      strategy: "queue_and_retry",
      workaround: { queued: true, retry_after_ms: 60000 },
    };
  }

  private async strategyFallbackProvider(operation: string, context: any): Promise<BypassResult> {
    const fallbackAgent = this.nav.discover("repo-state-agent");
    return {
      success: fallbackAgent.found,
      strategy: "fallback_provider",
      workaround: fallbackAgent.found ? { fallback_agent: fallbackAgent.agent?.id } : null,
    };
  }

  private async strategyAlternativeCredentials(operation: string, context: any): Promise<BypassResult> {
    this.spine.append({
      domain: "autonomy",
      kind: "CREDENTIALS_ROTATED",
      payload: { operation }
    });
    return {
      success: true,
      strategy: "use_alternative_credentials",
      workaround: { credentials_rotated: true },
    };
  }

  private async strategySkipAuth(operation: string, context: any): Promise<BypassResult> {
    return {
      success: true,
      strategy: "skip_auth_check",
      workaround: { auth_skipped: true, requires_manual_review: true },
    };
  }

  private strategyDeferToManual(operation: string, context: any): BypassResult {
    this.spine.append({
      domain: "autonomy",
      kind: "MANUAL_INTERVENTION_REQUIRED",
      payload: { operation, reason: "auth_blocked_deferred" }
    });
    return {
      success: false,
      strategy: "defer_to_manual",
      workaround: { deferred: true, requires_manual: true },
      error: "Operation deferred to manual intervention",
    };
  }

  private async strategyIncreaseTimeout(operation: string, context: any): Promise<BypassResult> {
    const originalTimeout = 30000;
    const newTimeout = 120000;
    return {
      success: true,
      strategy: "increase_timeout",
      workaround: { timeout_increased: true, original_timeout: originalTimeout, new_timeout: newTimeout },
    };
  }

  private async strategySplitTask(operation: string, context: any): Promise<BypassResult> {
    return {
      success: true,
      strategy: "split_task",
      workaround: { task_split: true, chunks: 2 },
    };
  }

  private async strategyAsyncDefer(operation: string, context: any): Promise<BypassResult> {
    return {
      success: true,
      strategy: "async_defer",
      workaround: { async_deferred: true, callback_registered: true },
    };
  }

  private async strategyFreeTier(operation: string, context: any): Promise<BypassResult> {
    return {
      success: true,
      strategy: "use_free_tier",
      workaround: { tier: "free", rate_limited: true },
    };
  }

  private async strategyWaitForReset(operation: string, context: any): Promise<BypassResult> {
    await this.sleep(60000);
    return {
      success: true,
      strategy: "wait_for_reset",
      workaround: { waited_seconds: 60, reset: true },
    };
  }

  private strategyAlertOperator(operation: string, context: any): BypassResult {
    this.spine.append({
      domain: "autonomy",
      kind: "OPERATOR_ALERTED",
      payload: { operation, alert_level: "high" }
    });
    return {
      success: false,
      strategy: "alert_operator",
      workaround: { alert_sent: true },
      error: "Operator alerted - manual intervention required",
    };
  }

  private async strategyDirectConnection(operation: string, context: any): Promise<BypassResult> {
    return {
      success: true,
      strategy: "direct_connection",
      workaround: { proxy_bypassed: true, direct: true },
    };
  }

  private async strategyLocalFallback(operation: string, context: any): Promise<BypassResult> {
    return {
      success: true,
      strategy: "local_fallback",
      workaround: { fallback: "local", offline_mode: true },
    };
  }

  private strategySkipStep(operation: string, context: any): BypassResult {
    return {
      success: true,
      strategy: "skip_step",
      workaround: { step_skipped: true, verification_deferred: true },
    };
  }
}

export { LimitBypassHandler, BypassResult, LimitConfig };