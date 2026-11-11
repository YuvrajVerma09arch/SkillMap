import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { get, post } from '../lib/api'

function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true)
    const s = document.createElement('script')
    s.src = 'https://checkout.razorpay.com/v1/checkout.js'
    s.onload = () => resolve(true)
    s.onerror = () => resolve(false)
    document.body.appendChild(s)
  })
}

const PLANS = [
  {
    id: 'starter',
    tier: 'TIER · 01',
    name: 'Starter',
    tagline: 'Explore the platform.',
    price: 0,
    period: '/forever',
    features: [
      { on: true, text: '5 AI Credits included' },
      { on: true, text: 'Basic job search' },
      { on: true, text: 'Company Prep Packs (free)' },
      { on: false, text: 'Featured profile' },
    ],
    cta: 'Current Plan',
    disabled: true,
  },
  {
    id: 'pro',
    tier: 'TIER · 02',
    name: 'Pro',
    tagline: 'For serious career builders.',
    price: 299,
    period: '/month',
    popular: true,
    features: [
      { on: true, text: '50 AI Credits', strong: true },
      { on: true, text: 'Unlimited roadmaps' },
      { on: true, text: 'Company Prep Packs' },
      { on: true, text: 'Featured profile' },
    ],
    cta: 'Upgrade to Pro →',
    primary: true,
  },
  {
    id: 'enterprise',
    tier: 'TIER · 03',
    name: 'Max',
    tagline: 'The ultimate power user plan.',
    price: 499,
    period: '/month',
    features: [
      { on: true, text: '200 AI Credits', strong: true },
      { on: true, text: 'Priority support' },
      { on: true, text: 'Early access features' },
      { on: true, text: 'Featured profile' },
    ],
    cta: 'Get Max →',
  },
]

export default function Pricing() {
  const { user, refresh } = useAuth()
  const { toast } = useToast()
  const [busy, setBusy] = useState(null)

  const buyPlan = async (planId) => {
    if (planId === 'starter') return
    if (!user) {
      toast('Sign in to upgrade your plan.', 'error')
      return
    }
    setBusy(planId)
    try {
      const ok = await loadRazorpay()
      if (!ok) {
        toast('Could not load Razorpay checkout.', 'error')
        return
      }
      const data = await post('/api/payments/create', { plan: planId })
      if (data.error) {
        toast(data.error, 'error')
        return
      }
      const rzp = new window.Razorpay({
        key: data.key_id,
        amount: data.amount,
        currency: 'INR',
        name: 'SkillMap AI',
        description: planId.toUpperCase() + ' Plan Upgrade',
        order_id: data.order_id,
        prefill: { name: data.user_name, email: data.user_email },
        theme: { color: '#e63946' },
        handler: async (resp) => {
          try {
            const verify = await post('/api/payments/verify', {
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            })
            if (verify.status === 'success') {
              toast(`Payment successful — ${verify.new_credits} credits available.`)
              refresh()
            } else {
              toast('Payment verification failed.', 'error')
            }
          } catch (err) {
            toast(err.message, 'error')
          }
        },
      })
      rzp.open()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '80px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 64 }}>
        <div className="section-label"><span className="label-signal">Pricing</span></div>
        <h1 className="display" style={{ fontSize: 'clamp(32px,5vw,56px)', color: 'var(--chalk)', marginBottom: 16 }}>
          Simple, transparent<br />credit pricing.
        </h1>
        <p style={{ fontSize: 15, color: 'var(--chalk-3)', maxWidth: 400, lineHeight: 1.7 }}>
          You currently have{' '}
          <span style={{ fontFamily: "'JetBrains Mono',monospace", color: 'var(--signal)', fontWeight: 600 }}>
            {user ? user.credits : 0} credits
          </span>{' '}
          remaining. Each AI operation costs one credit.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-px animate-fade-up" style={{ background: 'var(--wire)', animationDelay: '0.1s' }}>
        {PLANS.map((plan) => (
          <div key={plan.id} className={`plan-card${plan.popular ? ' featured' : ''}`}>
            {plan.popular ? (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
                <div className="label" style={{ color: 'var(--signal)' }}>{plan.tier}</div>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', background: 'var(--signal)', color: '#fff', padding: '3px 8px' }}>POPULAR</span>
              </div>
            ) : (
              <div className="label" style={{ marginBottom: 24 }}>{plan.tier}</div>
            )}

            <h2 className="display" style={{ fontSize: 22, color: 'var(--chalk)', marginBottom: 4 }}>{plan.name}</h2>
            <p style={{ fontSize: 12, color: 'var(--chalk-3)', marginBottom: 28 }}>{plan.tagline}</p>

            <div style={{ marginBottom: 32 }}>
              <span style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 48, fontWeight: 700, color: 'var(--chalk)', letterSpacing: '-0.03em' }}>₹{plan.price}</span>
              <span style={{ fontSize: 13, color: 'var(--chalk-3)', marginLeft: 6 }}>{plan.period}</span>
            </div>

            <div style={{ flex: 1, marginBottom: 32 }}>
              {plan.features.map((f, i) => (
                <div key={i} className={`feature-row${f.on ? '' : ' off'}`}>
                  <span style={{ color: f.on ? 'var(--signal)' : undefined, fontSize: 10 }}>{f.on ? '●' : '○'}</span>
                  {f.strong ? <strong style={{ color: 'var(--chalk)' }}>{f.text}</strong> : f.text}
                </div>
              ))}
            </div>

            <button
              onClick={() => buyPlan(plan.id)}
              disabled={plan.disabled || busy !== null}
              className={plan.primary ? 'btn-signal' : 'btn-ghost'}
              style={{ width: '100%', justifyContent: 'center', padding: '14px 24px', ...(plan.disabled ? { cursor: 'not-allowed', opacity: 0.5 } : {}) }}
            >
              {busy === plan.id ? 'Opening checkout…' : plan.cta}
            </button>
          </div>
        ))}
      </div>

      <div className="animate-fade-up" style={{ marginTop: 48, padding: '20px 24px', background: 'var(--ink-2)', border: '1px solid var(--wire)', borderLeft: '2px solid var(--signal)', animationDelay: '0.2s' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
          <i className="bi bi-info-circle" style={{ color: 'var(--signal)', fontSize: 16, marginTop: 1, flexShrink: 0 }}></i>
          <p style={{ fontSize: 13, color: 'var(--chalk-2)', lineHeight: 1.7 }}>
            Credits are consumed per AI operation: 5 credits per resume analysis, 1 per roadmap generation. Free accounts start with 5 credits. Company Prep Packs are free. Credits do not expire. Payments are processed securely via Razorpay.
          </p>
        </div>
      </div>
    </div>
  )
}
