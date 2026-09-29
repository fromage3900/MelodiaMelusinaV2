import assert from 'node:assert/strict'
import test from 'node:test'
import {
  SlidingWindowLimit,
  parseAiriEmoteOutput,
  validateIntent,
  validateMelodiaEvent,
} from '../protocol.mjs'

const event = changes => ({
  id: 'event-01',
  type: 'melodia.world.location',
  version: 1,
  timestamp: '2026-09-29T12:00:00.000Z',
  payload: { location: 'Sea Above' },
  ...changes,
})

test('valid semantic event is accepted', () => {
  assert.deepEqual(validateMelodiaEvent(event()), { ok: true, ignored: false })
})

test('malformed event envelope and payload are rejected', () => {
  assert.equal(validateMelodiaEvent({ ...event(), payload: { location: 22 } }).reason, 'malformed-payload')
  assert.equal(validateMelodiaEvent({ type: event().type }).reason, 'malformed-envelope')
  assert.equal(validateMelodiaEvent(event({ timestamp: 'today' })).reason, 'malformed-envelope')
})

test('unknown protocol version is rejected safely', () => {
  assert.equal(validateMelodiaEvent(event({ version: 99 })).reason, 'unsupported-version')
})

test('unknown event type is safely ignored', () => {
  assert.deepEqual(
    validateMelodiaEvent(event({ type: 'melodia.debug.execute' })),
    { ok: true, ignored: true, reason: 'unknown-event' },
  )
})

test('AIRI emote intent is typed and allowlisted', () => {
  const intent = {
    id: 'intent-01',
    type: 'melusina.emote',
    version: 1,
    timestamp: '2026-09-29T12:00:00.000Z',
    payload: { emotion: 'happy' },
  }
  assert.deepEqual(validateIntent(intent), { ok: true })
  assert.equal(validateIntent({ ...intent, type: 'unreal.exec' }).ok, false)
  assert.equal(validateIntent({ ...intent, payload: { emotion: 'launch_console' } }).ok, false)
  assert.equal(validateIntent({ ...intent, payload: { emotion: 'happy', command: 'quit' } }).ok, false)
})

test('AIRI ACT marker emits only an allowlisted emotion intent', () => {
  assert.deepEqual(parseAiriEmoteOutput('A small smile. <|ACT emotion="happy" intensity="0.7"|>'), { kind: 'intent', emotion: 'happy' })
  assert.deepEqual(parseAiriEmoteOutput('A quiet answer.'), { kind: 'ignore' })
  assert.equal(parseAiriEmoteOutput('<|ACT emotion="angry" intensity="0.7"|>').kind, 'reject')
  assert.equal(parseAiriEmoteOutput('<|ACT emotion="happy" intensity="1.7"|>').kind, 'reject')
  assert.equal(parseAiriEmoteOutput('<|ACT emotion="happy"|><|ACT emotion="sad"|>').kind, 'reject')
  assert.equal(parseAiriEmoteOutput('<|ACT emotion="happy"|> !melodia exec quit').emotion, 'happy')
})

test('sliding window throttles repeated requests', () => {
  const limit = new SlidingWindowLimit(2, 1000)
  assert.equal(limit.allow(100), true)
  assert.equal(limit.allow(200), true)
  assert.equal(limit.allow(300), false)
  assert.equal(limit.allow(1200), true)
})
