import { Keyboard } from '@maxhub/max-bot-api'
import { bot } from '../bot.js'
import type {
  MaxNotificationRequest,
} from '../types/notifications.js'
import {
  helperRequestKeyboard,
} from '../keyboards/mainKeyboard.js'

function buildText(payload: MaxNotificationRequest): string {
  if (payload.type === 'helper_request') {
    const request = payload.helper_request

    return [
      'Вызов помощника',
      '',
      `От: ${request.from}`,
      `Срочность: ${request.priority}`,
      `Тема: ${request.theme}`,
      `Создано: ${request.created_at}`,
      '',
      `Текст:\n${request.text || 'Без комментария'}`,
    ].join('\n')
  }

  if (payload.type === 'assigned') {
    const location = payload.location
      ? ` за столом ${payload.location}`
      : ''

    return [
      `Статус талона ${payload.talon.name} обновлён!`,
      `Оператор ожидает вас${location}.`,
    ].join('\n')
  }

  if (payload.type === 'called') {
    const location = payload.location
      ? ` за столом ${payload.location}`
      : ''

    return [
      `Повторный вызов талона ${payload.talon.name}!`,
      `Оператор ожидает вас${location}.`,
      '',
      'Пожалуйста, подойдите к оператору.',
      'Для просмотра своих талонов откройте меню.',
    ].join('\n')
  }

  if (payload.type === 'cancelled') {
    return [
      `Статус талона ${payload.talon.name} обновлён!`,
      'К сожалению, ваш талон больше недействителен.',
      'Чтобы взять новый талон, обратитесь на стойку ресепшена.',
    ].join('\n')
  }

  return [
    `Статус талона ${payload.talon.name} обновлён!`,
    'Спасибо, что обратились в Приёмную комиссию ДВФУ.',
    'Отзыв можно оставить в меню «Мои талоны».',
  ].join('\n')
}

function buildKeyboard(payload: MaxNotificationRequest) {
  if (payload.type === 'helper_request') {
    return helperRequestKeyboard(payload.helper_request.id)
  }

  return Keyboard.inlineKeyboard([
    [
      Keyboard.button.callback(
        'Мои талоны',
        'talons:list',
      ),
      Keyboard.button.callback(
        'Меню',
        'menu:main',
      ),
    ],
  ])
}

export async function sendMaxNotification(
  payload: MaxNotificationRequest,
): Promise<void> {
  const userId = Number(payload.external_user_id)

  if (!Number.isSafeInteger(userId)) {
    throw new Error(
      `Некорректный MAX user_id: ${payload.external_user_id}`,
    )
  }

  const maxApi = (bot as any).api

  await maxApi.sendMessageToUser(
    userId,
    buildText(payload),
    {
      attachments: [
        buildKeyboard(payload),
      ],
    },
  )
}