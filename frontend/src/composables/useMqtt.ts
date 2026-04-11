/**
 * MQTT 连接管理 composable
 */
import { ref, onMounted, onUnmounted } from 'vue'
import mqtt from 'mqtt'
import type { MqttClient } from 'mqtt'
import { useDeviceStore } from '@/stores/device'
import { MQTT_CONFIG, MQTT_TOPICS } from '@/utils/constants'

export function useMqtt() {
  const client = ref<MqttClient | null>(null)
  const connected = ref(false)
  const reconnecting = ref(false)
  const error = ref<string | null>(null)
  let connectAttempts = 0
  const MAX_ATTEMPTS = 10

  const deviceStore = useDeviceStore()

  /**
   * 连接MQTT服务器
   */
  async function connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 使用WebSocket连接
        const url = `${MQTT_CONFIG.protocol}://${MQTT_CONFIG.host}:${MQTT_CONFIG.port}/mqtt`
        
        client.value = mqtt.connect(url, {
          clientId: `${MQTT_CONFIG.clientIdPrefix}${Date.now()}`,
          clean: true,
          connectTimeout: MQTT_CONFIG.connectTimeout,
          keepalive: MQTT_CONFIG.keepalive,
          reconnectPeriod: MQTT_CONFIG.reconnectPeriod,
        })

        client.value.on('connect', () => {
          console.log('[MQTT] Connected successfully')
          connected.value = true
          reconnecting.value = false
          connectAttempts = 0
          subscribeAll()
          resolve()
        })

        client.value.on('message', handleIncomingMessage)

        client.value.on('error', (err) => {
          console.error('[MQTT] Error:', err)
          error.value = err.message
        })

        client.value.on('close', () => {
          console.log('[MQTT] Connection closed')
          connected.value = false
        })

        client.value.offline = () => {
          console.warn('[MQTT] Client went offline')
          connected.value = false
          reconnecting.value = true
        }

        client.value.reconnect = () => {
          connectAttempts++
          console.log(`[MQTT] Reconnecting... attempt ${connectAttempts}`)
          if (connectAttempts > MAX_ATTEMPTS) {
            error.value = `重连${MAX_ATTEMPTS}次失败，请检查网络`
            client.value?.end()
          }
        }
      } catch (e: any) {
        error.value = e.message
        reject(e)
      }
    })
  }

  /**
   * 订阅所有需要的主题
   */
  function subscribeAll() {
    if (!client.value) return

    const topics = Object.values(MQTT_TOPICS)
    topics.forEach(topic => {
      client.value!.subscribe(topic, { qos: 1 }, (err) => {
        if (err) console.error(`[MQTT] Subscribe failed for ${topic}:`, err)
        else console.log(`[MQTT] Subscribed to ${topic}`)
      })
    })
  }

  /**
   * 处理收到的消息
   */
  function handleIncomingMessage(topic: string, message: Buffer) {
    try {
      const payload = JSON.parse(message.toString())
      const mac = payload?.mac || ''

      switch (topic) {
        case MQTT_TOPICS.ONLINE:
          deviceStore.deviceOnline(mac)
          break
        case MQTT_TOPICS.OFFLINE:
          deviceStore.deviceOffline(mac)
          break
        case MQTT_TOPICS.BATTERY_REPLY:
          deviceStore.updateDeviceStatus(mac, { voltage: payload.voltage })
          break
        case MQTT_TOPICS.LED_REPLY:
          console.log(`[MQTT] LED reply from ${mac}:`, payload.result)
          break
        case MQTT_TOPICS.REBOOT_REPLY:
          console.log(`[MQTT] Reboot reply from ${mac}:`, payload.result)
          break
        default:
          console.log(`[MQTT] [${topic}]`, payload)
      }
    } catch {
      // 非JSON消息，忽略
    }
  }

  /**
   * 发布消息到指定主题
   */
  function publish(topic: string, data: Record<string, any>) {
    return new Promise<void>((resolve, reject) => {
      if (!client.value || !connected.value) {
        reject(new Error('MQTT未连接'))
        return
      }
      client.value!.publish(
        topic,
        JSON.stringify(data),
        { qos: 1 },
        (err) => err ? reject(err) : resolve()
      )
    })
  }

  /**
   * 断开连接
   */
  function disconnect() {
    if (client.value) {
      client.value.end(true)
      client.value = null
      connected.value = false
    }
  }

  return {
    connected,
    reconnecting,
    error,
    connect,
    disconnect,
    publish,
  }
}
