# Production SMTP Configuration Guide

## Overview
This guide covers setting up production-grade email verification for the ICP Hosting Platform.

## Supported Email Providers

### 1. SendGrid (Recommended)
SendGrid is highly reliable, has excellent deliverability, and provides detailed analytics.

**Setup:**
1. Sign up at https://sendgrid.com
2. Create an API key with Mail Send permission
3. Add sender verification: https://app.sendgrid.com/settings/sender_auth

**Environment Variables:**
```bash
SMTP_PROVIDER=sendgrid
SENDGRID_API_KEY=your_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Canistra
```

### 2. AWS SES (Simple Email Service)
AWS SES is cost-effective and scalable for high-volume email.

**Setup:**
1. Create AWS account and set up SES
2. Verify domain: https://console.aws.amazon.com/ses
3. Request production access (exit sandbox)
4. Create SMTP credentials

**Environment Variables:**
```bash
SMTP_PROVIDER=aws_ses
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY_ID=your_access_key
AWS_SES_SECRET_ACCESS_KEY=your_secret_key
AWS_SES_FROM_EMAIL=noreply@yourdomain.com
```

### 3. Mailgun
Mailgun offers excellent developer experience and rich APIs.

**Setup:**
1. Sign up at https://mailgun.com
2. Add domain: https://app.mailgun.com/app/domains
3. Verify domain with DNS records
4. Get API key: https://app.mailgun.com/app/account/security/api_keys

**Environment Variables:**
```bash
SMTP_PROVIDER=mailgun
MAILGUN_API_KEY=your_api_key_here
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
```

### 4. Postmark
Postmark specializes in transactional email with excellent template support.

**Setup:**
1. Sign up at https://postmarkapp.com
2. Create server: https://account.postmarkapp.com/servers
3. Set up sender signature
4. Get API token

**Environment Variables:**
```bash
SMTP_PROVIDER=postmark
POSTMARK_SERVER_TOKEN=your_token_here
POSTMARK_FROM_EMAIL=noreply@yourdomain.com
POSTMARK_FROM_NAME=Canistra
```

## Email Templates

### Verification Email
- Subject: "Verify Your Email - ICP Hosting Platform"
- Used for: User signup email verification
- Template: `templates/email-verification.html`

### Password Reset Email
- Subject: "Reset Your Password - ICP Hosting Platform"
- Used for: Password recovery
- Template: `templates/password-reset.html`

### Welcome Email
- Subject: "Welcome to Canistra - ICP Hosting Platform"
- Used for: After successful email verification
- Template: `templates/welcome.html`

### Deployment Notification
- Subject: "Your Project Has Been Deployed"
- Used for: Notify when project deployment completes
- Template: `templates/deployment-complete.html`

### Error Notification
- Subject: "Alert: Deployment Failed"
- Used for: Notify of deployment failures
- Template: `templates/deployment-failed.html`

## Configuration Steps

### Step 1: Choose Provider
Select the email provider that best fits your needs:
- **SendGrid**: Best for most use cases
- **AWS SES**: Best for cost-sensitive, high-volume scenarios
- **Mailgun**: Best for developer experience
- **Postmark**: Best for transactional email reliability

### Step 2: Set Up DNS Records
For all providers, you need to verify domain ownership via DNS:

**DKIM Record** (Domain Keys Identified Mail):
- Improves email authenticity
- Provided by email service
- Add to DNS: TXT record

**SPF Record** (Sender Policy Framework):
```
v=spf1 include:sendgrid.net ~all
# or for AWS SES:
v=spf1 include:amazonses.com ~all
```

**DMARC Record** (Domain-based Message Authentication):
```
v=DMARC1; p=quarantine; rua=mailto:admin@yourdomain.com
```

### Step 3: Configure Backend
Add to `.env`:
```bash
# Email Configuration
SMTP_PROVIDER=sendgrid  # or aws_ses, mailgun, postmark
SENDGRID_API_KEY=your_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Canistra

# Email Templates
EMAIL_TEMPLATE_DIR=/backend/app/templates/emails
VERIFICATION_EMAIL_TEMPLATE=email-verification.html
PASSWORD_RESET_EMAIL_TEMPLATE=password-reset.html

# Email Configuration
EMAIL_VERIFICATION_EXPIRY_HOURS=24
PASSWORD_RESET_EXPIRY_HOURS=1
```

### Step 4: Update Email Service
See `/backend/app/utils/email.py` for production email sending implementation.

### Step 5: Test Email Sending
```bash
# Test endpoint
curl -X POST http://localhost:8000/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Step 6: Set Up Email Monitoring
- SendGrid: Dashboard at https://app.sendgrid.com
- AWS SES: CloudWatch metrics and bounce handling
- Mailgun: Dashboard at https://app.mailgun.com
- Postmark: Dashboard at https://account.postmarkapp.com

## Email Verification Flow

### Signup Process
1. User submits email and password
2. System generates verification token (URL-safe, 32 bytes)
3. Email sent with verification link
4. User clicks link
5. Email marked as verified

**Verification Link Format:**
```
https://yourdomain.com/verify-email?token=XXXXXXXXXXXXXXXXXXXXX
```

### Token Security
- Tokens are cryptographically random
- Tokens expire after 24 hours
- Tokens are one-time use only
- Tokens are deleted after successful verification

## Password Reset Flow

1. User requests password reset
2. System generates reset token
3. Email sent with reset link
4. User clicks link and creates new password
5. Token is invalidated

**Reset Link Format:**
```
https://yourdomain.com/reset-password?token=XXXXXXXXXXXXXXXXXXXXX
```

## Rate Limiting

Prevent email spam with rate limiting:
- **Signup verification**: 5 attempts per hour per email
- **Password reset**: 3 attempts per hour per email
- **General emails**: 100 per day per user

## Deliverability Best Practices

1. **Keep lists clean**: Remove bounced/unsubscribed addresses
2. **Monitor bounce rates**: Target <1% hard bounces
3. **Use authentication**: Implement SPF, DKIM, DMARC
4. **Test templates**: Use Email on Acid or similar
5. **Monitor reputation**: Check at https://www.mxtoolbox.com
6. **Personalize**: Use recipient name when possible
7. **Provide unsubscribe**: Required for marketing emails
8. **Segment lists**: Send relevant content to segments

## Monitoring and Alerts

### Key Metrics
- Delivery rate (target: >99%)
- Bounce rate (target: <1%)
- Open rate (target: >15%)
- Click rate (target: >2%)
- Complaint rate (target: <0.1%)

### Setup Alerts
```yaml
# SendGrid Event Webhook
POST /api/v1/webhooks/sendgrid
- bounce
- dropped
- delivered
- opens
- clicks
```

## Troubleshooting

### Emails Not Being Delivered
1. Check DNS records (SPF, DKIM, DMARC)
2. Verify sender email is verified
3. Check spam/junk folder
4. Review bounce logs
5. Check rate limits

### High Bounce Rate
1. Verify email list quality
2. Check for typos in sender email
3. Implement list validation
4. Check ISP feedback loops

### Low Open Rates
1. Improve subject lines
2. Send at optimal times
3. Segment audience
4. Test preview text
5. A/B test templates

## Additional Resources

- SendGrid Documentation: https://docs.sendgrid.com
- AWS SES Documentation: https://docs.aws.amazon.com/ses/
- Mailgun Documentation: https://documentation.mailgun.com
- Postmark Documentation: https://postmarkapp.com/developer
- Email on Acid: https://www.emailonacid.com
- Return Path: https://www.returnpath.com
