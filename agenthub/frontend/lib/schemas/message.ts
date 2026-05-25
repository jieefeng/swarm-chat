import { z } from 'zod'

export const sendMessageSchema = z.object({
  content: z.string().min(1, '消息不能为空').max(5000, '消息过长'),
})

export type SendMessageInput = z.infer<typeof sendMessageSchema>
