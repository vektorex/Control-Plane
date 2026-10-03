/**
 * Webhook Signature Verification Utility for JavaScript SDK.
 * Supports Node.js crypto module and browser-safe fallback.
 */

import crypto from "crypto";

export function verifyWebhookSignature(payload, signatureHeader, secret, toleranceSeconds = 300) {
  if (!payload || !signatureHeader || !secret) {
    return false;
  }

  // Parse header: t=12345,v1=abcdef...
  const parts = {};
  const segments = signatureHeader.split(",");
  for (const seg of segments) {
    const [k, v] = seg.trim().split("=");
    if (k && v) {
      parts[k] = v;
    }
  }

  const timestamp = parseInt(parts.t, 10);
  const signature = parts.v1;

  if (isNaN(timestamp) || !signature) {
    return false;
  }

  // Check tolerance / replay attack window
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - timestamp) > toleranceSeconds) {
    return false;
  }

  // Compute expected HMAC-SHA256 signature
  const payloadString = typeof payload === "string" ? payload : JSON.stringify(payload);
  const signedPayload = `${timestamp}.${payloadString}`;

  const expected = crypto
    .createHmac("sha256", secret)
    .update(signedPayload, "utf8")
    .digest("hex");

  // Constant-time comparison
  try {
    const a = Buffer.from(signature, "hex");
    const b = Buffer.from(expected, "hex");
    if (a.length !== b.length) {
      return false;
    }
    return crypto.timingSafeEqual(a, b);
  } catch {
    return signature === expected;
  }
}
