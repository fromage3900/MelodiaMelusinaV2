export function createAudioReactiveBus({
  audioElement,
  fftSize = 1024,
  smoothing = 0.82,
} = {}) {
  if (!audioElement) throw new Error('createAudioReactiveBus requires an audio element.');

  let context = null;
  let analyser = null;
  let source = null;
  let frequencyData = null;

  async function start() {
    if (!context) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) throw new Error('Web Audio API is not supported in this browser.');

      context = new AudioContextClass();
      analyser = context.createAnalyser();
      analyser.fftSize = fftSize;
      analyser.smoothingTimeConstant = Math.min(0.99, Math.max(0, smoothing));
      frequencyData = new Uint8Array(analyser.frequencyBinCount);

      source = context.createMediaElementSource(audioElement);
      source.connect(analyser);
      analyser.connect(context.destination);
    }

    if (context.state === 'suspended') await context.resume();
    return context.state;
  }

  function read() {
    if (!analyser || !frequencyData) {
      return { level: 0, low: 0, mid: 0, high: 0, bins: null };
    }

    analyser.getByteFrequencyData(frequencyData);

    const average = (start, end) => {
      const safeStart = Math.max(0, Math.min(frequencyData.length, start));
      const safeEnd = Math.max(safeStart + 1, Math.min(frequencyData.length, end));
      let sum = 0;
      for (let i = safeStart; i < safeEnd; i += 1) sum += frequencyData[i];
      return (sum / (safeEnd - safeStart)) / 255;
    };

    const third = Math.max(1, Math.floor(frequencyData.length / 3));
    const low = average(0, third);
    const mid = average(third, third * 2);
    const high = average(third * 2, frequencyData.length);

    return {
      level: (low + mid + high) / 3,
      low,
      mid,
      high,
      bins: frequencyData,
    };
  }

  async function dispose() {
    source?.disconnect();
    analyser?.disconnect();
    if (context && context.state !== 'closed') await context.close();
    context = null;
    analyser = null;
    source = null;
    frequencyData = null;
  }

  return { start, read, dispose };
}
