import { Keyboard } from '@maxhub/max-bot-api'

export function mainKeyboard() {
  return Keyboard.inlineKeyboard([
    [
      Keyboard.button.callback(
        'Мои талоны',
        'talons:list',
      ),
    ],
    [
      Keyboard.button.callback(
        'Подписаться',
        'talons:subscribe',
        {
          intent: 'positive',
        },
      ),
    ],
    [
      Keyboard.button.callback(
        'Помощник',
        'helper:menu',
      ),
    ],
  ])
}

export function backToMenuKeyboard() {
  return Keyboard.inlineKeyboard([
    [
      Keyboard.button.callback(
        'Меню',
        'menu:main',
      ),
    ],
  ])
}

export function talonKeyboard(
  talonId: number,
  hasComment: boolean,
) {
  const reviewButton = hasComment
    ? Keyboard.button.callback(
      'Мой отзыв',
      `talon:comment:${talonId}`,
    )
    : Keyboard.button.callback(
      'Оставить отзыв',
      `talon:comment:add:${talonId}`,
      {
        intent: 'positive',
      },
    )

  return Keyboard.inlineKeyboard([
    [reviewButton],
    [
      Keyboard.button.callback(
        'Назад',
        'talons:list',
      ),
      Keyboard.button.callback(
        'Меню',
        'menu:main',
      ),
    ],
  ])
}

export function helperKeyboard(isActive: boolean) {
  return Keyboard.inlineKeyboard([
    [
      Keyboard.button.callback(
        isActive ? 'Стать неактивным' : 'Стать активным',
        'helper:toggle',
        {
          intent: isActive ? 'negative' : 'positive',
        },
      ),
    ],
    [
      Keyboard.button.callback(
        'Активные заявки',
        'helper:requests',
      ),
    ],
    [
      Keyboard.button.callback(
        'Меню',
        'menu:main',
      ),
    ],
  ])
}

export function helperRequestKeyboard(requestId: number) {
  return Keyboard.inlineKeyboard([
    [
      Keyboard.button.callback(
        'Выполнить',
        `helper:complete:${requestId}`,
        {
          intent: 'positive',
        },
      ),
    ],
    [
      Keyboard.button.callback(
        'Активные заявки',
        'helper:requests',
      ),
      Keyboard.button.callback(
        'Меню',
        'menu:main',
      ),
    ],
  ])
}