/**
 * 后端 WebSocket 连接 - 接收MQTT桥接的实时数据
 * 连接: /ws/device-status
 */
import { ref, type Ref, onMounted, onUnmounted } from 'vue'
import { useDeviceStore } from '@/stores/device'
import { formatVolt } from '@/utils/format'

const connected = ref(false)
const mqttConnected = ref(false)
const wsRef: Ref<WebSocket | null> = ref(null)
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

/** 全局活动记录 (供 RecentActivity 等组件使用) */
export const activities = ref<ActivityItem[]>([])
export interface ActivityItem {
  id: number
  text: string
  detail?: string
  time: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
}
let activityIdCounter = 0

/** 电量百分比计算: <335(3.35V)=0%, >390(3.90V)=100% */
function calcPct(v: number): string {
  if (v >= 390) return '100.0'
  if (v <= 335) return '0.0'
  return (((v - 335) / (390 - 335)) * 100).toFixed(1)
}

/** 内部消息事件总线 (keyed by message type) */
type MessageHandler = (data: any) => void
const _listeners: Map<string, Set<MessageHandler>> = new Map()

export function onWsMessage(type: string, handler: MessageHandler) {
  if (!_listeners.has(type)) _listeners.set(type, new Set())
  _listeners.get(type)!.add(handler)
}

export function offWsMessage(type: string, handler: MessageHandler) {
  _listeners.get(type)?.delete(handler)
}

export function useBackendWs() {
  const deviceStore = useDeviceStore()

  function connect() {
    if (wsRef.value?.readyState === WebSocket.OPEN) return

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/device-status`

    try {
      const ws = new WebSocket(url)
      wsRef.value = ws

      ws.onopen = () => {
        console.log('[WS] ✅ 后端WebSocket已连接')
        connected.value = true
        // 添加连接成功的活动记录
        addActivity('success', 'WebSocket连接已建立', '实时设备状态推送已启用')
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          handleMessage(msg)
        } catch {
          // 忽略非JSON消息
        }
      }

      ws.onclose = () => {
        console.log('[WS] 后端WebSocket断开')
        connected.value = false
        mqttConnected.value = false
        scheduleReconnect()
      }

      ws.onerror = (err) => {
        console.error('[WS] 错误:', err)
        connected.value = false
      }
    } catch (e) {
      console.error('[WS] 创建失败:', e)
      connected.value = false
      scheduleReconnect()
    }
  }

  function handleMessage(msg: any) {
    const { type, data } = msg

    // 通知外部监听器
    const handlers = _listeners.get(type)
    if (handlers) handlers.forEach(h => h(data))

    switch (type) {
      case 'connected': {
        const wasConnected = mqttConnected.value
        mqttConnected.value = !!msg.data?.mqtt_connected
        console.log(`[WS] 后端MQTT状态: ${mqttConnected.value ? '已连接' : '未连接'}`)
        
        // 添加MQTT连接状态变化的活动记录
        if (mqttConnected.value && !wasConnected) {
          addActivity('success', 'MQTT Broker连接成功', '已连接到设备状态服务器')
        } else if (!mqttConnected.value && wasConnected) {
          addActivity('warning', 'MQTT Broker连接断开', '设备状态更新暂停')
        }
        break
      }

      case 'online': {
        const mac = data?.mac
        if (mac) {
          deviceStore.deviceOnline(mac)
          addActivity('success', `设备 ${mac} 上线`, `msgId: ${data?.msgId ?? '--'}`)
        }
        break
      }

      case 'offline': {
        const mac = data?.mac
        if (mac) {
          deviceStore.deviceOffline(mac)
          addActivity('danger', `设备 ${mac} 已离线`, `msgId: ${data?.msgId ?? '--'}`)
        }
        break
      }

      case 'button': {
        const mac = data?.mac
        const btn = data?.button ?? '--'
        if (mac) {
          addActivity('info', `设备 ${mac} 按键触发`, `按键: ${btn}, 按压时长: ${data?.pressTime ?? '--'}ms`)
        }
        break
      }

      case 'battery_reply': {
        const mac = data?.mac
        const voltage = data?.voltage ?? data?.voltage_mv
        if (mac && voltage != null) {
          deviceStore.updateDeviceStatus(mac, { voltage })
          const level = voltage < 335 ? 'warning' : 'success'
          addActivity(level, `设备 ${mac} 电量更新`, `${formatVolt(voltage)} (~${calcPct(voltage)}%)`)
        }
        break
      }

      case 'led_reply':
      case 'reboot_reply':
      case 'display_reply': {
        const mac = data?.mac
        const result = data?.result ?? data?.code
        if (mac) {
          const ok = result === 200 || result === 0 || result === 'success'
          addActivity(ok ? 'primary' : 'warning', `设备 ${mac} ${type.replace('_reply', '')} ${ok ? '成功' : '失败'}`, JSON.stringify(data).slice(0, 80))
        }
        break
      }

      default:
        console.log('[WS] 未处理消息类型:', type, data)
    }
  }

  /** 添加一条活动记录（最多保留50条） */
  function addActivity(type: ActivityItem['type'], text: string, detail?: string) {
    const now = new Date()
    const timeStr = now.toLocaleTimeString('zh-CN', { hour12: false })
    activityIdCounter += 1
    activities.value.unshift({ id: activityIdCounter, text, detail, time: timeStr, type })
    if (activities.value.length > 50) activities.value.pop()
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (wsRef.value) {
      wsRef.value.close()
      wsRef.value = null
    }
    connected.value = false
    mqttConnected.value = false
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, 3000)
  }

  onMounted(() => connect())
  onUnmounted(() => disconnect())

  return { connected, mqttConnected, connect, disconnect }
}
