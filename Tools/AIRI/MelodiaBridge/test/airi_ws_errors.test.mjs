import assert from 'node:assert/strict'
import test from 'node:test'
import { createAiriWsClient } from '../airi_ws.mjs'

function withFakeSocket(fn, { failAuthenticate = false } = {}) {
  const Original = globalThis.WebSocket
  const sockets = []
  class FakeSocket {
    constructor(url) {
      this.url = url
      sockets.push(this)
    }
    send(text) {
      if (failAuthenticate && JSON.parse(text).type === 'module:authenticate')
        throw new Error('auth send failed')
    }
    close() {
      this.onclose?.({ code: 1000 })
    }
    serverSend(type, data) {
      this.onmessage?.({ data: JSON.stringify({ type, data }) })
    }
  }
  globalThis.WebSocket = FakeSocket
  return Promise.resolve().then(() => fn(sockets)).finally(() => {
    globalThis.WebSocket = Original
  })
}

test('token authentication send failure rejects immediately, not after timeout', async () => {
  await withFakeSocket(async sockets => {
    const client = createAiriWsClient({
      name: 'melodia.airi-bridge',
      url: 'ws://127.0.0.1:1/ws',
      token: 'test-token',
      connectTimeoutMs: 100,
    })
    try {
      const pending = client.connect()
      sockets[0].onopen()
      await assert.rejects(pending, /auth send failed/)
    }
    finally {
      client.close()
    }
  }, { failAuthenticate: true })
})

test('server handshake rejection reports actual failure before timeout', async () => {
  await withFakeSocket(async sockets => {
    const client = createAiriWsClient({
      name: 'melodia.airi-bridge',
      url: 'ws://127.0.0.1:1/ws',
      connectTimeoutMs: 100,
    })
    try {
      const pending = client.connect()
      sockets[0].onopen()
      sockets[0].serverSend('error', { message: 'module rejected' })
      await assert.rejects(pending, /module rejected.*AIRI_TOKEN/)
      assert.equal(client.isReady, false)
    }
    finally {
      client.close()
    }
  })
})
