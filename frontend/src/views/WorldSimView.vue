<template>
  <div class="world-sim">
    <!-- Header -->
    <header class="ws-header">
      <div class="ws-brand" @click="router.push('/')">MEGAFISH OFFLINE</div>
      <div class="ws-title">
        <span class="ws-title-icon">🌍</span>
        World Simulation Engine
      </div>
      <div class="ws-badge">8.3B Agents</div>
    </header>

    <div class="ws-body">
      <!-- INPUT PANEL -->
      <div v-if="phase === 'input'" class="input-panel">
        <div class="input-card">
          <div class="input-card-header">
            <div class="input-card-title">Scenario</div>
            <div class="input-card-subtitle">Describe the event or change you want to simulate. MegaFish will scan today's world, distribute it across all 8.3 billion people, and project forward.</div>
          </div>

          <textarea
            v-model="scenario"
            class="scenario-input"
            placeholder="e.g. A breakthrough AI model is released that can perform 90% of white-collar jobs..."
            rows="5"
          ></textarea>

          <div class="config-row">
            <div class="config-item">
              <label>Simulation Date</label>
              <input v-model="simDate" type="date" class="config-input" />
            </div>
            <div class="config-item">
              <label>Future Time Steps</label>
              <select v-model="timeSteps" class="config-input">
                <option :value="1">1 step (short term)</option>
                <option :value="2">2 steps</option>
                <option :value="3">3 steps (medium term)</option>
                <option :value="5">5 steps (long range)</option>
              </select>
            </div>
            <div class="config-item">
              <label>Population Sample</label>
              <select v-model="maxCohorts" class="config-input">
                <option :value="50">50 cohorts (fast)</option>
                <option :value="100">100 cohorts</option>
                <option :value="200">200 cohorts</option>
                <option :value="500">500 cohorts (full)</option>
              </select>
            </div>
          </div>

          <div class="input-footer">
            <div class="input-info">
              <span class="info-dot"></span>
              World news will be scanned live for {{ simDate }}
            </div>
            <button class="run-btn" :disabled="!scenario.trim()" @click="startSim">
              Run World Simulation →
            </button>
          </div>
        </div>
      </div>

      <!-- RUNNING PANEL -->
      <div v-else-if="phase === 'running'" class="running-panel">
        <div class="running-card">
          <div class="running-globe">🌍</div>
          <div class="running-title">Simulating 8.3 Billion People...</div>
          <div class="running-message">{{ statusMessage }}</div>
          <div class="progress-bar-wrap">
            <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="progress-label">{{ progress }}%</div>
          <div class="running-scenario">"{{ scenario }}"</div>
        </div>
      </div>

      <!-- RESULTS PANEL -->
      <div v-else-if="phase === 'done'" class="results-panel">
        <!-- Top Bar -->
        <div class="results-topbar">
          <div class="results-scenario">"{{ scenario }}"</div>
          <button class="new-sim-btn" @click="reset">+ New Simulation</button>
        </div>

        <!-- Global Sentiment -->
        <div class="results-section">
          <div class="section-label">Global Reaction — {{ result.total_population_simulated?.toLocaleString() }} people represented</div>
          <div class="sentiment-overview">
            <div
              v-for="(agg, domain) in result.initial_domains"
              :key="domain"
              class="sentiment-card"
              :class="sentimentClass(agg.sentiment_score)"
            >
              <div class="sentiment-domain">{{ domain }}</div>
              <div class="sentiment-bar-wrap">
                <div
                  class="sentiment-bar-fill"
                  :style="{ width: Math.abs(agg.sentiment_score / 2 * 100) + '%', background: sentimentColor(agg.sentiment_score) }"
                ></div>
              </div>
              <div class="sentiment-score">{{ formatScore(agg.sentiment_score) }}</div>
            </div>
          </div>
        </div>

        <!-- Two columns: By Region + By Income -->
        <div class="results-grid-2">
          <div class="results-section">
            <div class="section-label">By Region</div>
            <div class="breakdown-list">
              <div
                v-for="(data, region) in result.by_region"
                :key="region"
                class="breakdown-item"
              >
                <div class="breakdown-name">{{ region }}</div>
                <div class="breakdown-bar-wrap">
                  <div
                    class="breakdown-bar"
                    :style="{
                      width: barWidth(data.sentiment, result.by_region) + '%',
                      background: sentimentColor(data.sentiment)
                    }"
                  ></div>
                </div>
                <div class="breakdown-score">{{ formatScore(data.sentiment) }}</div>
                <div class="breakdown-pop">{{ formatPop(data.population) }}</div>
              </div>
            </div>
          </div>

          <div class="results-section">
            <div class="section-label">By Income Level</div>
            <div class="breakdown-list">
              <div
                v-for="(data, income) in result.by_income"
                :key="income"
                class="breakdown-item"
              >
                <div class="breakdown-name">{{ income.replace(/_/g, ' ') }}</div>
                <div class="breakdown-bar-wrap">
                  <div
                    class="breakdown-bar"
                    :style="{
                      width: barWidth(data.sentiment, result.by_income) + '%',
                      background: sentimentColor(data.sentiment)
                    }"
                  ></div>
                </div>
                <div class="breakdown-score">{{ formatScore(data.sentiment) }}</div>
                <div class="breakdown-pop">{{ formatPop(data.population) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Affected Cohorts -->
        <div class="results-grid-3">
          <div class="results-section">
            <div class="section-label">Most Supportive Groups</div>
            <div v-for="c in result.most_supportive" :key="c.cohort_id" class="cohort-card positive">
              <div class="cohort-name">{{ c.description || c.cohort_id.replace(/_/g, ' ') }}</div>
              <div class="cohort-pop">{{ formatPop(c.population) }}</div>
            </div>
          </div>
          <div class="results-section">
            <div class="section-label">Most Opposed Groups</div>
            <div v-for="c in result.most_opposed" :key="c.cohort_id" class="cohort-card negative">
              <div class="cohort-name">{{ c.description || c.cohort_id.replace(/_/g, ' ') }}</div>
              <div class="cohort-pop">{{ formatPop(c.population) }}</div>
            </div>
          </div>
          <div class="results-section">
            <div class="section-label">Most Affected Groups</div>
            <div v-for="c in result.most_affected" :key="c.cohort_id" class="cohort-card neutral">
              <div class="cohort-name">{{ c.description || c.cohort_id.replace(/_/g, ' ') }}</div>
              <div class="cohort-pop">{{ formatPop(c.population) }}</div>
            </div>
          </div>
        </div>

        <!-- Time Steps -->
        <div v-if="result.time_steps && result.time_steps.length" class="results-section">
          <div class="section-label">Future Projections</div>
          <div class="timeline">
            <div
              v-for="step in result.time_steps"
              :key="step.step"
              class="timeline-step"
            >
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-date">Step {{ step.step }} — {{ step.date }}</div>
                <div class="timeline-evolution">{{ step.scenario_evolution }}</div>
                <div class="timeline-developments">
                  <div v-for="(dev, i) in step.key_developments" :key="i" class="timeline-dev">
                    • {{ dev }}
                  </div>
                </div>
                <div v-if="step.global_sentiment !== undefined" class="timeline-sentiment">
                  <span
                    class="timeline-badge"
                    :style="{ background: sentimentColor(step.global_sentiment) + '22', color: sentimentColor(step.global_sentiment), border: '1px solid ' + sentimentColor(step.global_sentiment) + '55' }"
                  >global mood: {{ formatScore(step.global_sentiment) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ERROR PANEL -->
      <div v-else-if="phase === 'error'" class="error-panel">
        <div class="error-card">
          <div class="error-icon">✗</div>
          <div class="error-title">Simulation Failed</div>
          <div class="error-message">{{ errorMsg }}</div>
          <button class="run-btn" @click="reset">Try Again</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { startWorldSimulation, getWorldSimulationStatus } from '../api/simulation'

const router = useRouter()

// State
const phase = ref('input')       // input | running | done | error
const scenario = ref('')
const simDate = ref(new Date().toISOString().split('T')[0])
const timeSteps = ref(2)
const maxCohorts = ref(100)

const progress = ref(0)
const statusMessage = ref('Initializing...')
const result = ref(null)
const errorMsg = ref('')

let pollTimer = null

const startSim = async () => {
  phase.value = 'running'
  progress.value = 0
  statusMessage.value = 'Scanning world events...'

  try {
    const res = await startWorldSimulation({
      scenario: scenario.value,
      date: simDate.value,
      time_steps: timeSteps.value,
      max_cohorts: maxCohorts.value
    })

    if (!res.success) {
      phase.value = 'error'
      errorMsg.value = res.error || 'Failed to start simulation'
      return
    }

    const simId = res.simulation_id
    pollTimer = setInterval(async () => {
      try {
        const status = await getWorldSimulationStatus(simId)
        progress.value = status.progress || 0
        statusMessage.value = status.message || '...'

        if (status.status === 'completed') {
          clearInterval(pollTimer)
          result.value = status.result
          phase.value = 'done'
        } else if (status.status === 'failed') {
          clearInterval(pollTimer)
          phase.value = 'error'
          errorMsg.value = status.error || 'Simulation failed'
        }
      } catch (e) {
        // network hiccup — keep polling
      }
    }, 3000)
  } catch (e) {
    phase.value = 'error'
    errorMsg.value = e.message
  }
}

const reset = () => {
  clearInterval(pollTimer)
  phase.value = 'input'
  result.value = null
  progress.value = 0
  errorMsg.value = ''
}

onUnmounted(() => clearInterval(pollTimer))

// Helpers
const formatScore = (score) => {
  if (score === null || score === undefined) return '—'
  const v = parseFloat(score)
  return (v > 0 ? '+' : '') + v.toFixed(2)
}

const formatPop = (n) => {
  if (!n) return ''
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K'
  return n.toLocaleString()
}

const sentimentColor = (score) => {
  if (score === null || score === undefined) return '#999'
  const v = parseFloat(score)
  if (v >= 1.0) return '#22c55e'
  if (v >= 0.3) return '#84cc16'
  if (v >= -0.3) return '#f59e0b'
  if (v >= -1.0) return '#f97316'
  return '#ef4444'
}

const sentimentClass = (score) => {
  const v = parseFloat(score)
  if (v >= 0.3) return 'positive'
  if (v <= -0.3) return 'negative'
  return 'neutral'
}

const barWidth = (score, group) => {
  const max = Math.max(...Object.values(group).map(d => Math.abs(d.sentiment || 0)))
  if (!max) return 0
  return (Math.abs(score || 0) / max * 100)
}
</script>

<style scoped>
.world-sim {
  min-height: 100vh;
  background: #0a0a0a;
  color: #e8e8e8;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
}

/* Header */
.ws-header {
  height: 60px;
  background: #111;
  border-bottom: 1px solid #222;
  display: flex;
  align-items: center;
  padding: 0 32px;
  gap: 24px;
}

.ws-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 16px;
  letter-spacing: 1px;
  cursor: pointer;
  color: #fff;
}

.ws-title {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #aaa;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ws-title-icon { font-size: 18px; }

.ws-badge {
  background: #FF4500;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  letter-spacing: 0.5px;
}

/* Body */
.ws-body {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 40px 32px;
  overflow-y: auto;
}

/* Input Panel */
.input-panel {
  width: 100%;
  max-width: 800px;
}

.input-card {
  background: #111;
  border: 1px solid #222;
  padding: 32px;
}

.input-card-header {
  margin-bottom: 24px;
}

.input-card-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}

.input-card-subtitle {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.scenario-input {
  width: 100%;
  background: #0a0a0a;
  border: 1px solid #333;
  color: #e8e8e8;
  padding: 16px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.scenario-input:focus { border-color: #FF4500; }
.scenario-input::placeholder { color: #555; }

.config-row {
  display: flex;
  gap: 16px;
  margin-top: 20px;
}

.config-item {
  flex: 1;
}

.config-item label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.config-input {
  width: 100%;
  background: #0a0a0a;
  border: 1px solid #333;
  color: #e8e8e8;
  padding: 8px 12px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  box-sizing: border-box;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
}

.input-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #555;
}

.info-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
}

.run-btn {
  background: #FF4500;
  color: #fff;
  border: none;
  padding: 12px 28px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
  font-family: inherit;
  letter-spacing: 0.3px;
}

.run-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.run-btn:not(:disabled):hover { opacity: 0.85; }

/* Running Panel */
.running-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding-top: 60px;
}

.running-card {
  text-align: center;
  max-width: 500px;
}

.running-globe {
  font-size: 64px;
  animation: spin 4s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.running-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 20px 0 8px;
}

.running-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 24px;
  min-height: 20px;
}

.progress-bar-wrap {
  height: 4px;
  background: #222;
  margin: 0 auto 8px;
  max-width: 400px;
}

.progress-bar-fill {
  height: 100%;
  background: #FF4500;
  transition: width 0.5s ease;
}

.progress-label {
  font-size: 12px;
  color: #555;
  font-family: 'JetBrains Mono', monospace;
}

.running-scenario {
  margin-top: 24px;
  font-size: 13px;
  color: #444;
  font-style: italic;
  max-width: 360px;
  margin-left: auto;
  margin-right: auto;
}

/* Results Panel */
.results-panel {
  width: 100%;
  max-width: 1100px;
}

.results-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 32px;
}

.results-scenario {
  font-size: 16px;
  font-weight: 600;
  color: #ccc;
  font-style: italic;
  flex: 1;
}

.new-sim-btn {
  background: transparent;
  border: 1px solid #333;
  color: #aaa;
  padding: 8px 18px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
  transition: all 0.2s;
}
.new-sim-btn:hover { border-color: #FF4500; color: #FF4500; }

.results-section {
  background: #111;
  border: 1px solid #1e1e1e;
  padding: 24px;
  margin-bottom: 16px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

/* Sentiment overview */
.sentiment-overview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.sentiment-card {
  flex: 1;
  min-width: 140px;
  background: #0a0a0a;
  border: 1px solid #1e1e1e;
  padding: 12px 16px;
}

.sentiment-domain {
  font-size: 11px;
  font-weight: 700;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.sentiment-bar-wrap {
  height: 3px;
  background: #1a1a1a;
  margin-bottom: 6px;
}

.sentiment-bar-fill {
  height: 100%;
  transition: width 0.5s;
}

.sentiment-score {
  font-size: 20px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.sentiment-card.positive .sentiment-score { color: #22c55e; }
.sentiment-card.negative .sentiment-score { color: #ef4444; }
.sentiment-card.neutral .sentiment-score { color: #f59e0b; }

/* Grid layouts */
.results-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.results-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* Breakdown */
.breakdown-list { display: flex; flex-direction: column; gap: 8px; }

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.breakdown-name {
  width: 140px;
  color: #aaa;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 0;
}

.breakdown-bar-wrap {
  flex: 1;
  height: 4px;
  background: #1a1a1a;
}

.breakdown-bar {
  height: 100%;
  transition: width 0.5s;
}

.breakdown-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #777;
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

.breakdown-pop {
  font-size: 11px;
  color: #444;
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

/* Cohort cards */
.cohort-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-left: 3px solid;
  margin-bottom: 6px;
  font-size: 13px;
  background: #0a0a0a;
}

.cohort-card.positive { border-color: #22c55e; }
.cohort-card.negative { border-color: #ef4444; }
.cohort-card.neutral { border-color: #f59e0b; }

.cohort-name { color: #bbb; }
.cohort-pop { font-size: 11px; color: #555; font-family: 'JetBrains Mono', monospace; }

/* Timeline */
.timeline { display: flex; flex-direction: column; gap: 0; position: relative; }

.timeline::before {
  content: '';
  position: absolute;
  left: 10px;
  top: 20px;
  bottom: 20px;
  width: 1px;
  background: #222;
}

.timeline-step {
  display: flex;
  gap: 24px;
  padding: 0 0 24px 0;
  position: relative;
}

.timeline-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FF4500;
  flex-shrink: 0;
  margin-top: 2px;
  z-index: 1;
}

.timeline-content { flex: 1; }

.timeline-date {
  font-size: 11px;
  font-weight: 700;
  color: #FF4500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  font-family: 'JetBrains Mono', monospace;
}

.timeline-evolution {
  font-size: 14px;
  color: #ccc;
  line-height: 1.5;
  margin-bottom: 10px;
}

.timeline-developments {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.timeline-dev {
  font-size: 13px;
  color: #777;
  line-height: 1.4;
}

.timeline-sentiment {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.timeline-badge {
  font-size: 11px;
  padding: 2px 8px;
  font-family: 'JetBrains Mono', monospace;
}

/* Error Panel */
.error-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding-top: 60px;
}

.error-card {
  text-align: center;
  max-width: 400px;
}

.error-icon {
  font-size: 40px;
  color: #ef4444;
  margin-bottom: 16px;
}

.error-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}

.error-message {
  font-size: 13px;
  color: #666;
  margin-bottom: 24px;
  line-height: 1.5;
}
</style>
