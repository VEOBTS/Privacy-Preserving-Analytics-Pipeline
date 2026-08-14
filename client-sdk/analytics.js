/**
 * Privacy-Preserving Analytics SDK
 * 
 * Usage:
 *   <script src='http://your-server/sdk/analytics.js'></script>
 *   <script>
 *     await PrivacyAnalytics.init('http://your-server');
 *     await PrivacyAnalytics.track('video_complete', 1);
 *   </script>
 */

const PrivacyAnalytics = (() => {
  let serverUrl = '';
  let publicKeyN = null;   // BigInt: the Paillier modulus
  let initialized = false;

  // ── Utility: generate a cryptographically random BigInt in [2, max) ──────
  function randomBigInt(max) {
    const maxBytes = Math.ceil(max.toString(16).length / 2);
    let r;
    do {
      const bytes = crypto.getRandomValues(new Uint8Array(maxBytes));
      r = BigInt('0x' + Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join(''));
    } while (r < 2n || r >= max);
    return r;
  }

  // ── Utility: modular exponentiation (a^b mod m) ──────────────────────────
  // This is required for Paillier encryption.
  // JavaScript BigInt does not have a built-in modpow, so we implement it.
  function modpow(base, exp, mod) {
    let result = 1n;
    base = base % mod;
    while (exp > 0n) {
      if (exp % 2n === 1n) result = (result * base) % mod;
      exp = exp / 2n;
      base = (base * base) % mod;
    }
    return result;
  }

  // ── Paillier Encryption ───────────────────────────────────────────────────
  function paillierEncrypt(message, n) {
    const n2 = n * n;
    const g = n + 1n;       // Standard simplification: g = n + 1
    const r = randomBigInt(n);
    // Formula: ciphertext = (g^m mod n^2) * (r^n mod n^2) mod n^2
    const gm = modpow(g, message, n2);
    const rn = modpow(r, n, n2);
    return (gm * rn) % n2;
  }

  // ── Differential Privacy: Laplacian Noise ─────────────────────────────────
  // Adds noise sampled from a Laplace distribution.
  // sensitivity=1 because each user contributes at most 1 event.
  // epsilon=1.0 is a moderate privacy guarantee.
  function laplacianNoise(sensitivity = 1.0, epsilon = 1.0) {
    const scale = sensitivity / epsilon;
    // Use the inverse CDF method: if U ~ Uniform(-0.5, 0.5), then
    // X = -scale * sign(U) * ln(1 - 2*|U|) ~ Laplace(0, scale)
    const u = Math.random() - 0.5;
    const sign = u >= 0 ? 1 : -1;
    return -scale * sign * Math.log(1 - 2 * Math.abs(u));
  }

  // ── Public API ────────────────────────────────────────────────────────────

  /**
   * init(url) — Call this once when your page loads.
   * Fetches the public key from the server.
   * @param {string} url - The base URL of your analytics backend
   */
  async function init(url) {
    serverUrl = url.replace(/\/$/, '');  // Remove trailing slash
    const response = await fetch(`${serverUrl}/analytics/pubkey`);
    if (!response.ok) throw new Error('Failed to fetch public key');
    const data = await response.json();
    publicKeyN = BigInt(data.n);
    initialized = true;
    console.log('[PrivacyAnalytics] Initialized. Public key loaded.');
  }

  /**
   * track(bucket, value) — Track an event.
   * Adds Laplacian noise, encrypts the value, and sends the ciphertext.
   * @param {string} bucket - Event type, e.g. 'video_complete'
   * @param {number} value  - The integer value to track (e.g. 1 for an event)
   */
  async function track(bucket, value) {
    if (!initialized) throw new Error('Call PrivacyAnalytics.init() first');

    // Step 1: Add differential privacy noise
    const noise = laplacianNoise(1.0, 1.0);
    // Multiply by 100 to preserve 2 decimal places as integers
    const noisyValue = Math.round((value + noise) * 100);

    // Paillier requires a positive integer.
    // We add a large offset (10000) to keep values positive even with noise.
    const adjustedValue = BigInt(noisyValue + 10000);

    // Step 2: Encrypt the noisy value using Paillier
    const ciphertext = paillierEncrypt(adjustedValue, publicKeyN);

    // Step 3: Send only the ciphertext — nothing identifying
    const response = await fetch(`${serverUrl}/analytics/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bucket: bucket,
        ciphertext: ciphertext.toString()  // Send as string (too large for JSON number)
      })
    });

    if (!response.ok) {
      console.error('[PrivacyAnalytics] Failed to send event');
    } else {
      console.log(`[PrivacyAnalytics] Event tracked: ${bucket}`);
    }
  }

  return { init, track };
})();

// Make available as a global for script tag usage
window.PrivacyAnalytics = PrivacyAnalytics;