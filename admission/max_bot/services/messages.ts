import { Keyboard } from '@maxhub/max-bot-api'

export const BotActions = {
    MAIN_MENU: 'main:menu',
    TALONS_LIST: 'talons:list',
    TALONS_SUBSCRIBE: 'talons:subscribe',
    HELPER_MENU: 'helper:menu',
} as const;

export function buildMainMenuKeyboard() {
    return Keyboard.inlineKeyboard([
        [
            Keyboard.button.callback('Мои талоны', BotActions.TALONS_LIST),
            Keyboard.button.callback('Подписаться', BotActions.TALONS_SUBSCRIBE),
        ],
        [
            Keyboard.button.callback('Помощник', BotActions.HELPER_MENU),
        ],
    ]);
}

export function buildBackToMenuKeyboard () {
    return Keyboard.inlineKeyboard([
        [
            Keyboard.button.callback('В главное меню', BotActions.MAIN_MENU),
        ],
    ]);
}

export function buildStartMessage(payload?: string | null) {
    const lines = [
        'Здравствуйте!',
        '',
        'Это бот электронной очереди Приемной комиссии ДВФУ.',
        '',
        'Здесь вы сможете:',
        '• подписаться на обновления по талону;',
        '• посмотреть свои талоны;',
        '• получить уведомление, когда оператор будет ожидать вас;',
        '• оставить отзыв после завершения приема.',
    ];

    if (payload) {
        lines.push(
            '',
            'Вы перешли по ссылке с параметром: ${payload}',
            'Позже бот сможет использовать этот параметр для подписки на талон.',
        );
    }
    lines.push('', 'Выберите действие:');

    return lines.join('\n');
}
