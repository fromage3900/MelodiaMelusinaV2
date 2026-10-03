import assert from 'node:assert/strict'
import test from 'node:test'
import {
  buildAnnounce,
  buildHeartbeatPing,
  buildHeartbeatPong,
  createAiriWsClient,
  isSelfAnnounced,
} from '../airi_ws.mjs'

test('announce payload carries module identity and possible events', () => {
  const announce = buildAnnounce({
    name: 'melodia.airi-bridge',
    instanceId: 'inst-1',
    possibleEvents: ['context:update', 'output:gen-ai:chat:message'],
  })
  assert.equal(announce.type, 'extension:module:announce')
  assert.equal(announce.data.name, 'melodia.airi-bridge')
  assert.equal(announce.data.identity.id, 'inst-1')
  assert.equal(announce.data.identity.extension.id, 'melodia.airi-bridge')
  assert.deepEqual(announce.data.possibleEvents, ['context:update', 'output:gen-ai:chat:message'])
})

test('self announce is recognized from announced and registry sync', () => {
  const self = { name: 'melodia.airi-bridge', extensionId: 'melodia.airi-bridge' }
  assert.equal(isSelfAnnounced({
    type: 'extension:module:announced',
    data: { name: 'melodia.airi-bridge', identity: { id: 'melodia.airi-bridge' } },
  }, self), true)
  assert.equal(isSelfAnnounced({
    type: 'registry:modules:sync',
    data: { modules: [{ name: 'other' }, { name: 'melodia.airi-bridge', identity: { id: 'melodia.airi-bridge' } }] },
  }, self), true)
  assert.equal(isSelfAnnounced({
    type: 'extension:module:announced',
    data: { name: 'melodia.airi-bridge', identity: { id: 'something-else' } },
  }, self), false)
  assert.equal(isSelfAnnounced({ type: 'module:status', data: {} }, self), false)
})

test('heartbeat ping/pong use the documented kinds', () => {
  assert.equal(buildHeartbeatPing().data.kind, 'ping')
  assert.equal(buildHeartbeatPong().data.kind, 'pong')
  assert.equal(buildHeartbeatPing().type, 'transport:connection:heartbeat')
})

test('full handshake, heartbeat, and event dispatch against a fake socket', async () => {
  const RealWebSocket = globalThis.WebSocket
  const sockets = []
  class FakeSocket {
    constructor(url) {
      this.url = url
      this.sent = []
      sockets.push(this)
    }

    send(text) {
      this.sent.push(JSON.parse(String(text)))
    }

    open() {
      this.onopen?.()
    }

    close() {
      this.onclose?.({ code: 1000, reason: '' })
    }

    serverSend(message) {
      this.onmessage?.({ data: JSON.stringify(message) })
    }
  }
  globalThis.WebSocket = FakeSocket
  try {
    const states = []
    const received = []
    const client = createAiriWsClient({
      name: 'melodia.airi-bridge',
      url: 'ws://127.0.0.1:1/ws',
      possibleEvents: ['context:update', 'output:gen-ai:chat:message'],
      onStateChange: ({ status }) => states.push(status),
    })
    const connected = client.connect()
    assert.equal(sockets.length, 1)
    sockets[0].open()
    const socket = sockets[0]
    assert.equal(socket.sent[0].type, 'extension:module:announce')
    assert.equal(socket.sent[0].data.name, 'melodia.airi-bridge')
    assert.equal(socket.sent[0].metadata.source.kind, 'plugin')
    assert.ok(socket.sent[0].metadata.event.id)
    socket.serverSend({
      type: 'extension:module:announced',
      data: { name: 'melodia.airi-bridge', identity: { id: 'melodia.airi-bridge' } },
    })
    await connected
    assert.equal(client.isReady, true)
    assert.deepEqual(states, ['connecting', 'announcing', 'ready'])

    assert.equal(client.send({ type: 'context:update', data: { contextId: 'melodia.world' } }), true)
    const forwarded = socket.sent.at(-1)
    assert.equal(forwarded.type, 'context:update')
    assert.equal(forwarded.metadata.source.plugin.id, 'melodia.airi-bridge')

    socket.serverSend({ type: 'transport:connection:heartbeat', data: { kind: 'ping', message: '🩵' } })
    assert.equal(socket.sent.at(-1).data.kind, 'pong')

    const off = client.onEvent('output:gen-ai:chat:message', event => received.push(event))
    socket.serverSend({ type: 'output:gen-ai:chat:message', data: { message: { content: '<|ACT emotion="happy" intensity="0.7"|>' } } })
    assert.equal(received.length, 1)
    off()
    client.close()
    assert.equal(client.isReady, false)
  }
  finally {
    globalThis.WebSocket = RealWebSocket
  }
})

test('token path authenticates before announcing', async () => {
  const RealWebSocket = globalThis.WebSocket
  const sockets = []
  class FakeSocket {
    constructor(url) {
      this.url = url
      this.sent = []
      sockets.push(this)
    }

    send(text) {
      this.sent.push(JSON.parse(String(text)))
    }

    open() {
      this.onopen?.()
    }

    close() {
      this.onclose?.({ code: 1000, reason: '' })
    }

    serverSend(message) {
      this.onmessage?.({ data: JSON.stringify(message) })
    }
  }
  globalThis.WebSocket = FakeSocket
  try {
    const states = []
    const client = createAiriWsClient({
      name: 'melodia.airi-bridge',
      url: 'ws://127.0.0.1:1/ws',
      token: 'secret',
      onStateChange: ({ status }) => states.push(status),
    })
    const connected = client.connect()
    sockets[0].open()
    assert.equal(sockets[0].sent[0].type, 'module:authenticate')
    sockets[0].serverSend({ type: 'module:authenticated', data: { authenticated: true } })
    assert.equal(sockets[0].sent[1].type, 'extension:module:announce')
    sockets[0].serverSend({
      type: 'registry:modules:sync',
      data: { modules: [{ name: 'melodia.airi-bridge', identity: { id: 'melodia.airi-bridge' } }] },
    })
    await connected
    assert.equal(client.isReady, true)
    assert.deepEqual(states, ['connecting', 'authenticating', 'announcing', 'ready'])
    client.close()
  }
  finally {
    globalThis.WebSocket = RealWebSocket
  }
})

test('client requires a name and fails closed before connect', () => {
  assert.throws(() => createAiriWsClient({}), /name is required/)
  const client = createAiriWsClient({ name: 'melodia.airi-bridge', url: 'ws://127.0.0.1:1/ws' })
  assert.equal(client.isReady, false)
  assert.equal(client.send({ type: 'context:update', data: {} }), false)
  const off = client.onEvent('output:gen-ai:chat:message', () => {})
  assert.equal(typeof off, 'function')
  off()
  client.close()
  assert.equal(client.connectionStatus, 'closed')
})
