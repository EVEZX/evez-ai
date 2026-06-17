import { canonicalize } from 'json-canonicalize';

/**
 * Creates a notification with canonical hash for audit trail
 * @param notification - Notification object
 * @returns Canonical JSON string for hashing
 */
export function createNotification(notification: Record<string, any>): string {
  const canonical = canonicalize(notification);
  return canonical;
}

/**
 * Example notification data for testing
 */
export const sampleNotification = {
  type: 'email',
  recipient: 'user@example.com',
  subject: 'Important Update',
  body: 'This is a test notification',
  timestamp: 1234567890,
  priority: 'high'
};
