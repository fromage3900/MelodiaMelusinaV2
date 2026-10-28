import assert from 'node:assert/strict'
import test from 'node:test'
import { readAiriBridgeHealth } from '../pi_health.mjs'

const response = body => ({ ok: true, json: async () => body })

test('Pi observer reads only fixed loopback health route and whitelists fields', async () => {
  let target
  let options
  const snapshot = await readAiriBridgeHealth({
    port: 8765,
    fetchImpl: async (url, opts) => {
      target = url
      options = opts
      return response({
        protocolVersion: 1, airiConnected: true,
        queueDepth: 2, eventsForwarded: 8, intentsAccepted: 3,
        token: 'not-for-models',
      })
    },
  })
  assert.equal(target, 'http://127.0.0.1:8765/v1/health')
  assert.equal(options.method, 'GET')
  assert.equal(options.redirect, 'error')
  assert.deepEqual(snapshot, {
    status: 'connected', protocolVersion: 1, airiConnected: true,
    queueDepth: 2, eventsForwarded: 8, intentsAccepted: 3,
  })
  assert.equal('token' in snapshot, false)
})

test('relay-only status is distinct from confirmed AIRI connection', async () => {
  const snapshot = await readAiriBridgeHealth({
    fetchImpl: async () => response({
      protocolVersion: 1, airiConnected: false,
      queueDepth: 0, eventsForwarded: 0, intentsAccepted: 0,
    }),
  })
  assert.equal(snapshot.status, 'relay-only')
})

test('unreachable relay reports offline without leaking request errors', async () => {
  const snapshot = await readAiriBridgeHealth({
    fetchImpl: async () => { throw new Error('secret token in provider exception') },
  })
  assert.deepEqual(snapshot, { status: 'offline', reason: 'bridge-unreachable' })
})

test('reject incompatible or incomplete health evidence', async () => {
  for (const malformed of [
    { protocolVersion: 2, airiConnected: true, queueDepth: 0, eventsForwarded: 1, intentsAccepted: 1 },
    { protocolVersion: 1, airiConnected: 'yes', queueDepth: 0, eventsForwarded: 1, intentsAccepted: 1 },
    { protocolVersion: 1, airiConnected: true, queueDepth: -1, eventsForwarded: 1, intentsAccepted: 1 },
    { protocolVersion: 1, airiConnected: true, queueDepth: 0, eventsForwarded: 1 },
  ]) {
    const snapshot = await readAiriBridgeHealth({
      fetchImpl: async () => response(malformed),
    })
    assert.equal(snapshot.status, 'incompatible')
  }
})

test('port must be valid before any network request', async () => {
  let called = false
  await assert.rejects(() => readAiriBridgeHealth({
    port: 0,
    fetchImpl: async () => { called = true },
  }), /invalid AIRI bridge port/)
  assert.equal(called, false)
})
