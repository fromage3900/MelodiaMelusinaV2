export const PROTOCOL_VERSION = 1
export const MAX_MESSAGE_BYTES = 8192
export const EMOTIONS = Object.freeze(['neutral', 'happy', 'curious', 'sad', 'surprised', 'determined'])

const isRecord = value => value !== null && typeof value === 'object' && !Array.isArray(value)
const hasExactKeys = (value, required, optional = []) => {
  const keys = Object.keys(value)
  return required.every(key => Object.hasOwn(value, key))
    && keys.every(key => required.includes(key) || optional.includes(key))
}
const validId = value => typeof value === 'string'
  && value.length > 0
  && value.length <= 80
  && /^[A-Za-z0-9._:-]+$/.test(value)
const validTimestamp = value => typeof value === 'string'
  && value.length <= 40
  && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
  && Number.isFinite(Date.parse(value))
const validLabel = value => typeof value === 'string'
  && value.length > 0
  && value.length <= 80
  && /^[\p{L}\p{N} .'-]+$/u.test(value)

const payloadValidators = {
  'melodia.world.location': payload =>
    hasExactKeys(payload, ['location']) && validLabel(payload.location),
  'melodia.world.phase': payload =>
    hasExactKeys(payload, ['phase']) && ['exploration', 'rhythm', 'combat', 'narrative'].includes(payload.phase),
  'melodia.melusina.state': payload =>
    hasExactKeys(payload, ['state']) && ['Exploring', 'Interacting', 'Performing', 'InRhythm', 'InCombat', 'Unavailable'].includes(payload.state),
  'melodia.rhythm.combo': payload =>
    hasExactKeys(payload, ['combo', 'accuracy'], ['instrument'])
    && Number.isSafeInteger(payload.combo)
    && payload.combo >= 0
    && typeof payload.accuracy === 'number'
    && Number.isFinite(payload.accuracy)
    && payload.accuracy >= 0
    && payload.accuracy <= 1
    && (payload.instrument === undefined || validLabel(payload.instrument)),
  'melodia.sir_melodious.distance': payload =>
    hasExactKeys(payload, ['distance_cm'], ['state'])
    && typeof payload.distance_cm === 'number'
    && Number.isFinite(payload.distance_cm)
    && payload.distance_cm >= 0
    && payload.distance_cm <= 100000
    && (payload.state === undefined || ['nearby', 'following', 'distant', 'unavailable'].includes(payload.state)),
}

export function validateMelodiaEvent(value) {
  if (!isRecord(value)
    || !hasExactKeys(value, ['id', 'type', 'version', 'timestamp', 'payload'])
    || !validId(value.id)
    || !validTimestamp(value.timestamp)
    || typeof value.type !== 'string'
    || value.type.length === 0
    || value.type.length > 100
    || !isRecord(value.payload)) {
    return { ok: false, reason: 'malformed-envelope' }
  }
  if (value.version !== PROTOCOL_VERSION)
    return { ok: false, reason: 'unsupported-version' }

  const validatePayload = payloadValidators[value.type]
  if (!validatePayload)
    return { ok: true, ignored: true, reason: 'unknown-event' }
  if (!validatePayload(value.payload))
    return { ok: false, reason: 'malformed-payload' }

  return { ok: true, ignored: false }
}

export function validateIntent(value) {
  if (!isRecord(value)
    || !hasExactKeys(value, ['id', 'type', 'version', 'timestamp', 'payload'])
    || !validId(value.id)
    || !validTimestamp(value.timestamp)
    || value.type.length > 100
    || value.type !== 'melusina.emote'
    || value.version !== PROTOCOL_VERSION
    || !isRecord(value.payload)
    || !hasExactKeys(value.payload, ['emotion'])
    || !EMOTIONS.includes(value.payload.emotion)) {
    return { ok: false, reason: 'unsupported-or-malformed-intent' }
  }
  return { ok: true }
}

export function parseAiriEmoteOutput(text) {
  if (typeof text !== 'string')
    return { kind: 'ignore' }

  if (text.length > MAX_MESSAGE_BYTES)
    return { kind: 'reject', reason: 'message-too-large' }

  const markers = text.match(/<\|ACT\b[\s\S]*?\|>/g) ?? []
  if (markers.length === 0)
    return { kind: 'ignore' }
  if (markers.length !== 1)
    return { kind: 'reject', reason: 'ambiguous-act-markers' }

  const match = /^<\|ACT emotion="(neutral|happy|curious|sad|surprised|determined)"(?: intensity="([^"]+)")?\|>$/.exec(markers[0])
  if (!match)
    return { kind: 'reject', reason: 'unsupported-or-malformed-act' }

  if (match[2] !== undefined) {
    const intensity = Number(match[2])
    if (!Number.isFinite(intensity) || intensity < 0 || intensity > 1)
      return { kind: 'reject', reason: 'invalid-act-intensity' }
  }

  return { kind: 'intent', emotion: match[1] }
}

export class SlidingWindowLimit {
  constructor(limit, windowMs = 60_000) {
    this.limit = limit
    this.windowMs = windowMs
    this.timestamps = []
  }

  allow(nowMs = Date.now()) {
    this.timestamps = this.timestamps.filter(timestamp => nowMs - timestamp < this.windowMs)
    if (this.timestamps.length >= this.limit)
      return false
    this.timestamps.push(nowMs)
    return true
  }
}
