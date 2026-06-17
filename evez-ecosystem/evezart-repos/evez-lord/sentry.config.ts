import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN || "https://steven-crawford-maggard.sentry.io",
  tracesSampleRate: 1.0,
  debug: false,
  environment: process.env.NODE_ENV,
});
