// Read-only Pi/AIRI canary: GET one fixed loopback health endpoint.
// This module does not dispatch intents, inspect UE assets, or write project state.

const PROTOCOL_VERSION = 1
const MAX_PORT = 65535

export async function readAiriBridgeHealth({
  port = Number(process.env.MELODIA_BRIDGE_PORT ?? 8765),
  fetchImpl = globalThis.fetch,
  signal,
} = {}) {
  if (!Number.isInteger(port) || port < 1 || port > MAX_PORT)
    throw new TypeError('invalid AIRI bridge port')

  try {
    const response = await fetchImpl(`http://127.0.0.1:${port}/v1/health`, {
      method: 'GET',
      redirect: 'error',
      signal: signal ?? AbortSignal.timeout(1500),
    })
    if (!response.ok)
      return { status: 'offline', reason: 'health-http-failure' }

    const data = await response.json()
    if (!data || data.protocolVersion !== PROTOCOL_VERSION
      || typeof data.airiConnected !== 'boolean'
      || !Number.isSafeInteger(data.queueDepth) || data.queueDepth < 0
      || !Number.isSafeInteger(data.eventsForwarded) || data.eventsForwarded < 0
      || !Number.isSafeInteger(data.intentsAccepted) || data.intentsAccepted < 0)
      return { status: 'incompatible', reason: 'invalid-health-contract' }

    return {
      status: data.airiConnected ? 'connected' : 'relay-only',
      protocolVersion: PROTOCOL_VERSION,
      airiConnected: data.airiConnected,
      queueDepth: data.queueDepth,
      eventsForwarded: data.eventsForwarded,
      intentsAccepted: data.intentsAccepted,
    }
  }
  catch {
    return { status: 'offline', reason: 'bridge-unreachable' }
  }
}
