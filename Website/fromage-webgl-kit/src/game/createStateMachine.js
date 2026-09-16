export function createStateMachine({ initial, states } = {}) {
  if (!initial) throw new Error('createStateMachine requires an initial state.');
  if (!states?.[initial]) throw new Error(`Unknown initial state: ${initial}`);

  let current = initial;
  const listeners = new Set();

  function snapshot() {
    return { state: current };
  }

  function can(event) {
    return Boolean(states[current]?.on?.[event]);
  }

  function send(event, payload) {
    const transition = states[current]?.on?.[event];
    if (!transition) return false;

    const next = typeof transition === 'string' ? transition : transition.target;
    if (!states[next]) throw new Error(`Unknown target state: ${next}`);

    const previous = current;
    if (typeof transition === 'object' && transition.guard && !transition.guard({ previous, payload })) {
      return false;
    }

    current = next;
    if (typeof transition === 'object' && transition.effect) {
      transition.effect({ previous, current, event, payload });
    }

    for (const listener of listeners) listener({ previous, current, event, payload });
    return true;
  }

  function subscribe(listener) {
    if (typeof listener !== 'function') throw new Error('subscribe requires a function.');
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  return { snapshot, can, send, subscribe };
}
