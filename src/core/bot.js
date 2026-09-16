const { Telegraf, Markup } = require('telegraf');
const config = require('../config/default');

if (!config.botToken) {
  throw new Error('TELEGRAM_BOT_TOKEN .env faylida topilmadi');
}

const bot = new Telegraf(config.botToken);

async function notifyOrderAccepted(telegramId) {
  await bot.telegram.sendMessage(
    telegramId,
    "Buyurtmangiz muvaffaqiyatli qabul qilindi! Kuryerimiz tez orada bog'lanadi 🍕"
  );
}

module.exports = { bot, Markup, notifyOrderAccepted };
