import assert from 'node:assert/strict'
import test from 'node:test'
import { createRelay } from '../relay.mjs'

const sampleEvent = {
  id: 'event-02',
  type: 'melodia.world.location',
  version: 1,
  timestamp: '2026-09-29T12:00:00.000Z',
  payload: { location: 'Sea Above' },
}

async function withRelay(options, run) {
  const relay = createRelay({ port: 0, ...options })
  const address = await relay.listen()
  try {
    await run('http://127.0.0.1:' + address.port, relay)
  }
  finally {
    await relay.close()
  }
}

test('loopback relay forwards a validated event through AIRI context:update', async () => {
  const sent = []
  const airiClient = { isReady: true, send(message) { sent.push(message); return true } }
  await withRelay({ airiClient }, async base => {
    const response = await fetch(base + '/v1/events', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(sampleEvent),
    })
    assert.equal(response.status, 202)
    assert.deepEqual(await response.json(), { accepted: true, forwarded: true })
    assert.equal(sent.length, 1)
    assert.equal(sent[0].type, 'context:update')
    assert.equal(sent[0].data.contextId, 'melodia.world')
    assert.equal(sent[0].data.strategy, 'replace-self')
    assert.deepEqual(JSON.parse(sent[0].data.text), sampleEvent)
  })
})

test('malformed events, unsupported versions, and unknown events fail closed', async () => {
  await withRelay({}, async base => {
    const post = body => fetch(base + '/v1/events', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    })
    assert.equal((await post({ type: sampleEvent.type })).status, 400)
    assert.equal((await post({ ...sampleEvent, version: 2 })).status, 409)
    const unknown = await post({ ...sampleEvent, type: 'melodia.exec.shell' })
    assert.equal(unknown.status, 202)
    assert.equal((await unknown.json()).ignored, true)
  })
})

test('relay accepts a semantic event when AIRI is offline without forwarding it', async () => {
  await withRelay({}, async base => {
    const response = await fetch(base + '/v1/events', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(sampleEvent),
    })
    assert.equal(response.status, 202)
    assert.deepEqual(await response.json(), { accepted: true, forwarded: false })
  })
})

test('only one explicit AIRI ACT emotion marker enters the Unreal intent queue', async () => {
  await withRelay({}, async (base, relay) => {
    assert.equal(relay.handleAiriOutput('That sounds difficult.'), false)
    assert.equal(relay.handleAiriOutput('<|ACT emotion="happy" intensity="0.6"|>'), true)
    const response = await fetch(base + '/v1/intents')
    const poll = await response.json()
    assert.equal(poll.type, 'melodia.bridge.intent_poll')
    assert.equal(poll.version, 1)
    assert.equal(typeof poll.timestamp, 'string')
    assert.equal(poll.payload.queueDepth, 0)
    assert.equal(typeof poll.payload.rejected, 'number')
    assert.equal(typeof poll.payload.airiConnected, 'boolean')
    assert.equal(poll.payload.intent.type, 'melusina.emote')
    assert.deepEqual(poll.payload.intent.payload, { emotion: 'happy' })
    assert.equal((await fetch(base + '/v1/intents').then(result => result.json())).payload.intent, null)
  })
})

test('event rate limit applies at the relay boundary', async () => {
  await withRelay({ eventLimit: 1, airiClient: { isReady: false } }, async base => {
    const post = () => fetch(base + '/v1/events', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(sampleEvent),
    })
    assert.equal((await post()).status, 202)
    assert.equal((await post()).status, 429)
  })
})
