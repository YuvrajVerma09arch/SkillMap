// Allowlist external-link schemes before putting a value into an <a href>.
//
// React 18 only *warns* about `javascript:` URLs (React 19 blocks them), and
// several hrefs in this app come from untrusted sources: user-entered company
// websites, third-party job feeds, and LLM/corpus output. A `javascript:` URL
// in an href is a stored-XSS vector, so reject anything that is not http(s).
//
// Returns a safe absolute http(s) URL, or undefined (React omits the href
// attribute) for anything else. Schemeless domains like "example.com" are
// upgraded to https:// rather than dropped, so legitimate legacy values keep
// working instead of breaking.
export function safeExternalHref(value) {
  if (typeof value !== 'string') return undefined
  const trimmed = value.trim()
  if (!trimmed) return undefined

  // Reject dangerous schemes explicitly before any URL parsing. This catches
  // `javascript:`, `data:`, `vbscript:` etc. even when obfuscated with case or
  // leading whitespace/control characters.
  if (/^\s*(?:javascript|data|vbscript)\s*:/i.test(trimmed)) return undefined

  try {
    const u = new URL(trimmed)
    if (u.protocol === 'http:' || u.protocol === 'https:') return u.href
    // Absolute URL with any other scheme (ftp:, file:, ...) — reject.
    if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed)) return undefined
  } catch {
    // Not an absolute URL — fall through to the schemeless upgrade below.
  }

  // Schemeless value (e.g. "example.com" or "//cdn.com"): upgrade to https.
  // Require a dotted hostname so relative paths and javascript-style strings
  // can never become a navigation target.
  try {
    const u = new URL(`https://${trimmed}`)
    return u.hostname.includes('.') ? u.href : undefined
  } catch {
    return undefined
  }
}
