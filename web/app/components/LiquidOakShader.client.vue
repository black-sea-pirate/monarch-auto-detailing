<script setup lang="ts">
const canvas = useTemplateRef<HTMLCanvasElement>('canvas')

let animationFrame = 0
let resizeObserver: ResizeObserver | undefined
let disposePointer: (() => void) | undefined

onMounted(() => {
  const element = canvas.value
  if (!element) return

  const gl = element.getContext('webgl', {
    alpha: true,
    antialias: false,
    powerPreference: 'low-power',
  })
  if (!gl) return

  initializeShader(element, gl)
})

function initializeShader(element: HTMLCanvasElement, gl: WebGLRenderingContext) {

  const vertexSource = `
    attribute vec2 a_position;
    varying vec2 v_texCoord;
    void main() {
      v_texCoord = a_position * 0.5 + 0.5;
      gl_Position = vec4(a_position, 0.0, 1.0);
    }
  `

  const fragmentSource = `
    precision highp float;
    varying vec2 v_texCoord;
    uniform float u_time;
    uniform vec2 u_resolution;
    uniform vec2 u_mouse;

    vec3 forest = vec3(0.055, 0.227, 0.184);
    vec3 graphite = vec3(0.027, 0.067, 0.055);
    vec3 oak = vec3(0.22, 0.13, 0.08);
    vec3 champagne = vec3(0.78, 0.65, 0.42);

    float hash(vec2 p) {
      p = fract(p * vec2(123.34, 456.21));
      p += dot(p, p + 45.32);
      return fract(p.x * p.y);
    }

    float noise(vec2 p) {
      vec2 i = floor(p);
      vec2 f = fract(p);
      float a = hash(i);
      float b = hash(i + vec2(1.0, 0.0));
      float c = hash(i + vec2(0.0, 1.0));
      float d = hash(i + vec2(1.0, 1.0));
      vec2 u = f * f * (3.0 - 2.0 * f);
      return mix(a, b, u.x) +
        (c - a) * u.y * (1.0 - u.x) +
        (d - b) * u.x * u.y;
    }

    void main() {
      vec2 uv = v_texCoord;
      vec2 pointer = u_mouse / max(u_resolution, vec2(1.0));
      float slow = u_time * 0.045;
      float grain = noise(vec2(uv.x * 3.0 + slow, uv.y * 7.0));
      float refraction = noise(uv * 2.2 + slow + pointer * 0.28) *
        noise(uv * 4.4 - slow * 1.6);
      float oakLine = smoothstep(0.42, 0.8, grain) * 0.22;
      vec3 color = mix(graphite, forest, uv.y * 0.44 + refraction * 0.35);
      color = mix(color, oak, oakLine);
      float shimmer = pow(noise(uv * 8.0 + slow * 2.0), 12.0);
      color = mix(color, champagne, shimmer * 0.10);
      float vignette = smoothstep(0.95, 0.25, length(uv - 0.5));
      color *= 0.62 + vignette * 0.38;
      gl_FragColor = vec4(color, 0.94);
    }
  `

  function createShader(type: number, source: string) {
    const shader = gl.createShader(type)
    if (!shader) return null
    gl.shaderSource(shader, source)
    gl.compileShader(shader)
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      gl.deleteShader(shader)
      return null
    }
    return shader
  }

  const vertexShader = createShader(gl.VERTEX_SHADER, vertexSource)
  const fragmentShader = createShader(gl.FRAGMENT_SHADER, fragmentSource)
  const program = gl.createProgram()
  if (!vertexShader || !fragmentShader || !program) return

  gl.attachShader(program, vertexShader)
  gl.attachShader(program, fragmentShader)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return
  gl.useProgram(program)

  const buffer = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
    gl.STATIC_DRAW,
  )

  const position = gl.getAttribLocation(program, 'a_position')
  gl.enableVertexAttribArray(position)
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0)

  const timeUniform = gl.getUniformLocation(program, 'u_time')
  const resolutionUniform = gl.getUniformLocation(program, 'u_resolution')
  const mouseUniform = gl.getUniformLocation(program, 'u_mouse')
  const pointer = { x: 0, y: 0 }

  function syncSize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5)
    const width = Math.max(1, Math.round(element.clientWidth * ratio))
    const height = Math.max(1, Math.round(element.clientHeight * ratio))
    if (element.width !== width || element.height !== height) {
      element.width = width
      element.height = height
    }
    if (!pointer.x && !pointer.y) {
      pointer.x = width / 2
      pointer.y = height / 2
    }
  }

  function handlePointer(event: PointerEvent) {
    const bounds = element.getBoundingClientRect()
    if (!bounds.width || !bounds.height) return
    pointer.x = ((event.clientX - bounds.left) / bounds.width) * element.width
    pointer.y = (1 - (event.clientY - bounds.top) / bounds.height) * element.height
  }

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  function render(time: number) {
    syncSize()
    gl.viewport(0, 0, element.width, element.height)
    gl.uniform1f(timeUniform, reducedMotion ? 0 : time * 0.001)
    gl.uniform2f(resolutionUniform, element.width, element.height)
    gl.uniform2f(mouseUniform, pointer.x, pointer.y)
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    if (!reducedMotion) animationFrame = requestAnimationFrame(render)
  }

  resizeObserver = new ResizeObserver(syncSize)
  resizeObserver.observe(element)
  element.addEventListener('pointermove', handlePointer, { passive: true })
  disposePointer = () => element.removeEventListener('pointermove', handlePointer)
  render(0)
}

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  disposePointer?.()
})
</script>

<template>
  <div class="liquid-oak-surface" aria-hidden="true">
    <canvas ref="canvas" class="liquid-oak-canvas" />
  </div>
</template>

<style scoped>
.liquid-oak-surface {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 72% 24%, rgb(199 165 108 / 18%), transparent 26%),
    radial-gradient(circle at 22% 72%, rgb(29 87 69 / 36%), transparent 38%),
    linear-gradient(125deg, #07110e, #123a2d 48%, #080f0d);
  background-size: 140% 140%;
  animation: fallback-refraction 12s ease-in-out infinite alternate;
}

.liquid-oak-surface::after {
  position: absolute;
  inset: -35%;
  opacity: 0.28;
  background: conic-gradient(from 110deg, transparent, rgb(224 194 140 / 12%), transparent 24%);
  animation: fallback-glint 14s linear infinite;
  content: '';
}

.liquid-oak-canvas {
  position: absolute;
  z-index: 1;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
}

@keyframes fallback-refraction {
  from { background-position: 0% 35%; }
  to { background-position: 100% 65%; }
}

@keyframes fallback-glint {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .liquid-oak-surface,
  .liquid-oak-surface::after { animation: none; }
}
</style>
