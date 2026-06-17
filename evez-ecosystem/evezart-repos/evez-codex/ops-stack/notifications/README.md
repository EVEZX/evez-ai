# Notifications Module

This module handles notification delivery and management across multiple channels.

## Features

- Multi-channel notification support (email, SMS, push)
- Template management
- Canonical data hashing for audit trails

## Usage

```typescript
import { createNotification } from './notifications/index.js';

const notification = {
  type: 'email',
  recipient: 'user@example.com',
  message: 'Hello World'
};
const hash = createNotification(notification);
console.log('Notification hash:', hash);
```

## Testing

This module includes golden hash tests to ensure deterministic canonicalization of notifications.
