// Regression test for the href scheme allowlist (SECURITY.md #4).
// Run from repo root:  node tests/test_safe_href.mjs
import { safeExternalHref } from '../frontend/src/lib/safeHref.js'

const cases = [
  ['https://example.com/x', 'https://example.com/x'],
  ['http://a.b', 'http://a.b/'],
  ['javascript:alert(1)', undefined],
  ['JaVaScRiPt:alert(1)', undefined],
  [' javascript:alert(1)', undefined],
  ['jav\tascript:alert(1)', undefined],
  [' data:text/html,x', undefined],
  ['vbscript:msgbox', undefined],
  ['file:///etc/passwd', undefined],
  ['ftp://x.com', undefined],
  ['example.com/path', 'https://example.com/path'],
  ['//cdn.com/x', 'https://cdn.com/x'],
  ['', undefined], [null, undefined], [undefined, undefined],
  ['relative/path', undefined],
  ['  https://ok.com  ', 'https://ok.com/'],
]

let fail = 0
for (const [input, want] of cases) {
  const got = safeExternalHref(input)
  const ok = got === want
  if (!ok) fail++
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${JSON.stringify(input)} -> ${JSON.stringify(got)} (want ${JSON.stringify(want)})`)
}
console.log(fail ? `\nFAIL: ${fail} case(s)` : '\nPASS: href scheme allowlist correct')
process.exit(fail ? 1 : 0)
