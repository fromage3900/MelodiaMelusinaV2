// Minimal dependency-free AIRI module client.
//
// Fallback when `@proj-airi/server-sdk` cannot be installed (its
// `@proj-airi/better-ws` dependency is workspace-only, registry E404).
// Implements only the subset the Melodia bridge needs, derived from the
// published SDK source (client.ts) and protocol event definitions:
//   - anonymous module handshake: `extension:module:announce` ->
//     `extension:module:announced` (or self entry in `registry:modules:sync`)
//   - `transport:connection:heartbeat` ping -> pong, plus periodic pings
//   - `send()` with the SDK's metadata envelope (plugin source + event id)
//   - `onEvent()` dispatch by message type (same surface relay.mjs expects:
//     `isReady`, `send()`, `onEvent()`)
//
// Wire format is plain JSON `{ type, data, metadata }`. The server also
// accepts SuperJSON; plain JSON is sufficient per the SDK codec fallback.
// Token authentication is supported when AIRI_TOKEN is provided;
// otherwise the client attempts the anonymous module announcement.

import { randomUUID } from 'node:crypto'

const createInstanceId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
const createEventId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`

export function buildAnnounce({ name, instanceId, possibleEvents = [] }) {
  return {
    type: 'extension:module:announce',
    data: {
      name,
      identity: { id: instanceId, extension: { id: name } },
      possibleEvents,
      dependencies: [],
    },
  }
}

export function buildHeartbeatPong() {
  return {
    type: 'transport:connection:heartbeat',
    data: { kind: 'pong', message: '💛', at: Date.now() },
  }
}

export function buildHeartbeatPing() {
  return {
    type: 'transport:connection:heartbeat',
    data: { kind: 'ping', message: '🩵', at: Date.now() },
  }
}

export function isSelfAnnounced(message, { name, extensionId }) {
  if (message?.type === 'extension:module:announced')
    return message?.data?.name === name && message?.data?.identity?.id === extensionId
  if (message?.type === 'registry:modules:sync')
    return Array.isArray(message?.data?.modules) && message.data.modules.some(module =>
      module?.name === name && module?.identity?.id === extensionId,
    )
  return false
}

export function createAiriWsClient({
  name,
  url = 'ws://localhost:6121/ws',
  token = process.env.AIRI_TOKEN || undefined,
  possibleEvents = [],
  connectTimeoutMs = 15000,
  heartbeatIntervalMs = 15000,
  onStateChange = () => {},
  onError = () => {},
} = {}) {
  if (!name)
    throw new Error('AIRI module name is required')
  const instanceId = createInstanceId()
  const extensionId = name
  const listeners = new Map()
  let socket = null
  let status = 'idle'
  let wantClose = false
  let reconnectDelayMs = 10000
  let consecutiveFailures = 0
  let generation = 0
  let heartbeatTimer = null
  let lastError = null

  const setStatus = (next) => {
    if (status === next)
      return
    const previousStatus = status
    status = next
    onStateChange({ previousStatus, status })
  }

  const withMetadata = data => ({
    ...data,
    metadata: {
      ...data.metadata,
      source: {
        kind: 'plugin',
        id: instanceId,
        extension: { id: name },
        plugin: { id: name },
      },
      event: { ...data.metadata?.event, id: data.metadata?.event?.id ?? createEventId() },
    },
  })

  const parseMessage = (text) => {
    try {
      const raw = String(text)
      // Server speaks SuperJSON; accept its `json` envelope or plain JSON.
      const superJson = JSON.parse(raw)
      const candidate = superJson && typeof superJson === 'object' && 'json' in superJson && 'type' in (superJson.json ?? {})
        ? superJson.json
        : superJson
      if (candidate && typeof candidate === 'object' && typeof candidate.type === 'string')
        return candidate
    }
    catch {}
    return null
  }

  const serverErrorText = message => (message?.type === 'error'
    && typeof message?.data?.message === 'string'
    ? message.data.message
    : null)

  const dispatch = (message) => {
    if (message?.type === 'transport:connection:heartbeat' && message?.data?.kind === 'ping') {
      try {
        socket?.send(JSON.stringify(withMetadata(buildHeartbeatPong())))
      }
      catch {}
      return
    }
    if (message?.type === 'error') {
      lastError = new Error(typeof message?.data?.message === 'string' ? message.data.message : 'AIRI server error')
      onError(lastError)
      return
    }
    const set = listeners.get(message?.type)
    if (!set?.size)
      return
    for (const listener of [...set]) {
      try {
        listener(message)
      }
      catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        onError(lastError)
      }
    }
  }

  const startHeartbeat = () => {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      try {
        socket?.send(JSON.stringify(withMetadata(buildHeartbeatPing())))
      }
      catch {}
    }, heartbeatIntervalMs)
    heartbeatTimer.unref?.()
  }

  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  const scheduleReconnect = (gen) => {
    if (wantClose || gen !== generation)
      return
    consecutiveFailures += 1
    // Calm backoff: a rejecting server (e.g. missing token) must not be
    // hammered. First retry at 10 s, doubling to a 60 s ceiling.
    reconnectDelayMs = Math.min(10000 * 2 ** Math.min(consecutiveFailures - 1, 3), 60000)
    setStatus('reconnecting')
    const timer = setTimeout(() => {
      if (!wantClose && gen === generation)
        void connect().catch(() => {})
    }, reconnectDelayMs)
    timer.unref?.()
  }

  async function connect() {
    if (status === 'ready')
      return
    wantClose = false
    generation += 1
    const gen = generation
    lastError = null
    setStatus('connecting')
    await new Promise((resolve, reject) => {
      let settled = false
      const timer = setTimeout(() => {
        if (!settled) {
          settled = true
          try {
            socket?.close()
          }
          catch {}
          reject(new Error(`AIRI connection timed out after ${connectTimeoutMs}ms`))
        }
      }, connectTimeoutMs)
      timer.unref?.()

      let ws
      try {
        ws = new WebSocket(url)
      }
      catch (error) {
        clearTimeout(timer)
        reject(error)
        return
      }
      socket = ws

      ws.onopen = () => {
        if (token) {
          setStatus('authenticating')
          try {
            ws.send(JSON.stringify(withMetadata({ type: 'module:authenticate', data: { token } })))
          }
          catch (error) {
            if (!settled) {
              settled = true
              clearTimeout(timer)
              reject(error)
            }
          }
          return
        }
        setStatus('announcing')
        try {
          ws.send(JSON.stringify(withMetadata(buildAnnounce({ name, instanceId, possibleEvents }))))
        }
        catch (error) {
          if (!settled) {
            settled = true
            clearTimeout(timer)
            reject(error)
          }
        }
      }
      ws.onmessage = (event) => {
        if (gen !== generation)
          return
        const message = parseMessage(event?.data)
        if (!message)
          return
        const errorText = serverErrorText(message)
        if (errorText) {
          const hint = !token ? ' (if AIRI requires authentication, set AIRI_TOKEN)' : ''
          lastError = new Error(errorText + hint)
          onError(lastError)
          if (!settled) {
            settled = true
            clearTimeout(timer)
            try {
              ws.close()
            }
            catch {}
            reject(lastError)
            return
          }
        }
        if (!settled) {
          if (token && message.type === 'module:authenticated' && message?.data?.authenticated === true) {
            setStatus('announcing')
            try {
              ws.send(JSON.stringify(withMetadata(buildAnnounce({ name, instanceId, possibleEvents }))))
            }
            catch (error) {
              settled = true
              clearTimeout(timer)
              reject(error)
            }
            return
          }
          if (isSelfAnnounced(message, { name, extensionId })) {
            settled = true
            clearTimeout(timer)
            consecutiveFailures = 0
            setStatus('ready')
            startHeartbeat()
            resolve()
            return
          }
          return
        }
        if (status === 'ready')
          dispatch(message)
      }
      ws.onerror = () => {
        // Error details arrive via close/server error events; avoid double-report.
      }
      ws.onclose = () => {
        stopHeartbeat()
        if (gen !== generation)
          return
        const wasReady = status === 'ready'
        socket = null
        if (!settled) {
          settled = true
          clearTimeout(timer)
          setStatus('closed')
          const failure = lastError ?? new Error('AIRI websocket closed before announce completed')
          lastError = failure
          scheduleReconnect(gen)
          reject(failure)
          return
        }
        if (!wantClose) {
          if (wasReady)
            onError(new Error('AIRI connection lost; reconnecting'))
          scheduleReconnect(gen)
        }
        else {
          setStatus('closed')
        }
      }
    })
  }

  return {
    get connectionStatus() {
      return status
    },
    get isReady() {
      return status === 'ready'
    },
    get lastError() {
      return lastError
    },
    connect,
    send(data) {
      if (status !== 'ready' || !socket)
        return false
      try {
        socket.send(JSON.stringify(withMetadata(data)))
        return true
      }
      catch {
        return false
      }
    },
    onEvent(type, callback) {
      let set = listeners.get(type)
      if (!set) {
        set = new Set()
        listeners.set(type, set)
      }
      set.add(callback)
      return () => {
        set.delete(callback)
        if (!set.size)
          listeners.delete(type)
      }
    },
    close() {
      wantClose = true
      generation += 1
      stopHeartbeat()
      try {
        socket?.close()
      }
      catch {}
      socket = null
      setStatus('closed')
    },
  }
}

export { randomUUID }
