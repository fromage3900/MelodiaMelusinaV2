import { createServer } from 'node:http'
import { randomUUID } from 'node:crypto'
import {
  MAX_MESSAGE_BYTES,
  PROTOCOL_VERSION,
  SlidingWindowLimit,
  parseAiriEmoteOutput,
  validateMelodiaEvent,
} from './protocol.mjs'

const readJson = request => new Promise((resolve, reject) => {
  const chunks = []
  let bytes = 0
  let tooLarge = false
  request.on('data', chunk => {
    bytes += chunk.length
    if (bytes > MAX_MESSAGE_BYTES) {
      tooLarge = true
      return
    }
    if (!tooLarge)
      chunks.push(chunk)
  })
  request.on('end', () => {
    if (tooLarge) {
      reject(Object.assign(new Error('message too large'), { statusCode: 413 }))
      return
    }
    try {
      resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')))
    }
    catch {
      reject(Object.assign(new Error('malformed JSON'), { statusCode: 400 }))
    }
  })
  request.on('error', reject)
})

const sendJson = (response, statusCode, value) => {
  response.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
  })
  response.end(JSON.stringify(value))
}

const makeTimestamp = now => new Date(now()).toISOString()

export function createRelay({
  airiClient = null,
  host = '127.0.0.1',
  port = 8765,
  now = Date.now,
  eventLimit = 30,
  intentLimit = 5,
  queueLimit = 8,
} = {}) {
  const eventRate = new SlidingWindowLimit(eventLimit)
  const intentRate = new SlidingWindowLimit(intentLimit)
  const intents = []
  const stats = {
    eventsReceived: 0,
    eventsForwarded: 0,
    intentsAccepted: 0,
    rejected: 0,
    ignored: 0,
    lastTx: null,
    lastRx: null,
  }

  const handleAiriOutput = text => {
    const parsed = parseAiriEmoteOutput(text)
    if (parsed.kind === 'ignore')
      return false
    if (parsed.kind === 'reject' || !intentRate.allow(now())) {
      stats.rejected += 1
      return false
    }
    if (intents.length >= queueLimit) {
      stats.rejected += 1
      return false
    }

    const intent = {
      id: randomUUID(),
      type: 'melusina.emote',
      version: PROTOCOL_VERSION,
      timestamp: makeTimestamp(now),
      payload: { emotion: parsed.emotion },
    }
    intents.push(intent)
    stats.intentsAccepted += 1
    stats.lastRx = intent.type
    return true
  }

  const server = createServer(async (request, response) => {
    const url = new URL(request.url ?? '/', 'http://127.0.0.1')

    if (request.method === 'GET' && url.pathname === '/v1/health') {
      sendJson(response, 200, {
        protocolVersion: PROTOCOL_VERSION,
        airiConnected: Boolean(airiClient?.isReady),
        ...stats,
        queueDepth: intents.length,
      })
      return
    }

    if (request.method === 'GET' && url.pathname === '/v1/intents') {
      sendJson(response, 200, {
        type: 'melodia.bridge.intent_poll',
        version: PROTOCOL_VERSION,
        timestamp: makeTimestamp(now),
        payload: {
          intent: intents.shift() ?? null,
          queueDepth: intents.length,
          rejected: stats.rejected,
          airiConnected: Boolean(airiClient?.isReady),
        },
      })
      return
    }

    if (request.method === 'POST' && url.pathname === '/v1/events') {
      let event
      try {
        event = await readJson(request)
      }
      catch (error) {
        stats.rejected += 1
        sendJson(response, error.statusCode ?? 400, { accepted: false, reason: error.message })
        return
      }

      const validation = validateMelodiaEvent(event)
      if (!validation.ok) {
        stats.rejected += 1
        const statusCode = validation.reason === 'unsupported-version' ? 409 : 400
        sendJson(response, statusCode, { accepted: false, reason: validation.reason })
        return
      }
      if (validation.ignored) {
        stats.ignored += 1
        sendJson(response, 202, { accepted: false, ignored: true, reason: validation.reason })
        return
      }
      if (!eventRate.allow(now())) {
        stats.rejected += 1
        sendJson(response, 429, { accepted: false, reason: 'rate-limited' })
        return
      }

      stats.eventsReceived += 1
      stats.lastTx = event.type
      let forwarded = false
      if (airiClient?.isReady) {
        try {
          forwarded = airiClient.send({
            type: 'context:update',
            data: {
              id: event.id,
              contextId: 'melodia.world',
              lane: 'melodia-world',
              strategy: 'replace-self',
              text: JSON.stringify(event),
              hints: ['Canonical, current-session game state. Do not infer fields that are not present.'],
            },
          })
        }
        catch {
          forwarded = false
        }
      }
      if (forwarded)
        stats.eventsForwarded += 1

      sendJson(response, 202, { accepted: true, forwarded })
      return
    }

    sendJson(response, 404, { accepted: false, reason: 'not-found' })
  })

  return {
    server,
    stats,
    handleAiriOutput,
    setAiriClient(client) {
      airiClient = client
    },
    listen() {
      return new Promise((resolve, reject) => {
        server.once('error', reject)
        server.listen(port, host, () => {
          server.off('error', reject)
          resolve(server.address())
        })
      })
    },
    close() {
      return new Promise((resolve, reject) => {
        if (!server.listening) {
          resolve()
          return
        }
        server.close(error => error ? reject(error) : resolve())
      })
    },
  }
}
