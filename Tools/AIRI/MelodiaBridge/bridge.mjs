import { createRelay } from './relay.mjs'

const port = Number(process.env.MELODIA_BRIDGE_PORT ?? 8765)
if (!Number.isInteger(port) || port < 1 || port > 65535)
  throw new Error('MELODIA_BRIDGE_PORT must be a valid TCP port')

const relay = createRelay({ port, host: '127.0.0.1' })
const address = await relay.listen()
console.info('Melodia AIRI relay listening on 127.0.0.1:' + address.port)

try {
  const { Client } = await import('@proj-airi/server-sdk')
  const client = new Client({
    name: 'melodia.airi-bridge',
    url: process.env.AIRI_WS_URL ?? 'ws://localhost:6121/ws',
    token: process.env.AIRI_TOKEN || undefined,
    possibleEvents: ['context:update', 'output:gen-ai:chat:message'],
    autoConnect: false,
    autoReconnect: true,
    onError: () => console.warn('AIRI connection error; local relay remains available'),
    onStateChange: state => console.info('AIRI connection state: ' + state.status),
  })
  relay.setAiriClient(client)
  client.onEvent('output:gen-ai:chat:message', event => {
    const content = event?.data?.message?.content
    const text = typeof content === 'string'
      ? content
      : Array.isArray(content)
        ? content.filter(part => part?.type === 'text' && typeof part.text === 'string').map(part => part.text).join('\n')
        : ''
    relay.handleAiriOutput(text)
  })
  client.connect().catch(() => {
    console.warn('AIRI is offline; Unreal events and intents will fail closed')
  })
}
catch {
  console.warn('AIRI Server SDK is unavailable; trying the dependency-free module client')
  try {
    const { createAiriWsClient } = await import('./airi_ws.mjs')
    const fallback = createAiriWsClient({
      name: 'melodia.airi-bridge',
      url: process.env.AIRI_WS_URL ?? 'ws://localhost:6121/ws',
      possibleEvents: ['context:update', 'output:gen-ai:chat:message'],
      onStateChange: state => console.info('AIRI connection state: ' + state.status),
      onError: () => console.warn('AIRI connection error; local relay remains available'),
    })
    relay.setAiriClient(fallback)
    fallback.onEvent('output:gen-ai:chat:message', event => {
      const content = event?.data?.message?.content
      const text = typeof content === 'string'
        ? content
        : Array.isArray(content)
          ? content.filter(part => part?.type === 'text' && typeof part.text === 'string').map(part => part.text).join('\n')
          : ''
      relay.handleAiriOutput(text)
    })
    await fallback.connect().catch(() => {
      console.warn('AIRI is offline; Unreal events and intents will fail closed')
    })
  }
  catch {
    console.warn('AIRI module client is unavailable; local relay remains available')
  }
}

process.on('SIGINT', () => {
  relay.close().then(() => process.exit(0))
})
