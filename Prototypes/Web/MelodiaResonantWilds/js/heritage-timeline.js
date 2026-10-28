export function createDeterministicTimeline({ duration, channels = {} } = {}) {
  if (!Number.isFinite(duration) || duration <= 0) {
    throw new Error('createDeterministicTimeline requires a positive duration.');
  }

  const normalizedChannels = Object.fromEntries(
    Object.entries(channels).map(([name, segments]) => {
      if (!Array.isArray(segments) || segments.length === 0) {
        throw new Error(`Timeline channel "${name}" requires at least one segment.`);
      }

      const ordered = segments
        .map((segment) => ({ ...segment }))
        .sort((a, b) => a.start - b.start);

      for (const segment of ordered) {
        if (!Number.isFinite(segment.start) || !Number.isFinite(segment.end) || segment.end < segment.start) {
          throw new Error(`Timeline channel "${name}" contains an invalid segment.`);
        }
        if (!Number.isFinite(segment.from) || !Number.isFinite(segment.to)) {
          throw new Error(`Timeline channel "${name}" segments require finite from/to values.`);
        }
      }

      return [name, ordered];
    }),
  );

  function clampTime(time) {
    if (!Number.isFinite(time)) return 0;
    return Math.min(duration, Math.max(0, time));
  }

  function sampleSegment(segment, time) {
    if (time <= segment.start) return segment.from;
    if (time >= segment.end) return segment.to;
    if (segment.end === segment.start) return segment.to;
    const u = (time - segment.start) / (segment.end - segment.start);
    return segment.from + (segment.to - segment.from) * u;
  }

  function sampleChannel(segments, time) {
    let value = segments[0].from;

    for (const segment of segments) {
      if (time < segment.start) break;
      value = sampleSegment(segment, time);
      if (time <= segment.end) break;
    }

    return value;
  }

  function sample(time) {
    const t = clampTime(time);
    const values = {};

    for (const [name, segments] of Object.entries(normalizedChannels)) {
      values[name] = sampleChannel(segments, t);
    }

    return { time: t, progress: t / duration, values };
  }

  function wrap(time) {
    if (!Number.isFinite(time)) return 0;
    const wrapped = time % duration;
    return wrapped < 0 ? wrapped + duration : wrapped;
  }

  return {
    duration,
    channels: normalizedChannels,
    sample,
    wrap,
  };
}
