const { Markup } = require('telegraf');
const config = require('../config/default');
const User = require('../models/User');

async function handleStart(ctx) {
  await User.findOrCreateUser({
    telegramId: ctx.from.id,
    firstName: ctx.from.first_name,
    lastName: ctx.from.last_name,
  });

  await ctx.reply(
    `Assalomu alaykum, ${ctx.from.first_name}! 🍕\n\nIssiqqina pizzalarni buyurtma qilish uchun quyidagi tugmani bosing.`,
    Markup.keyboard([Markup.button.webApp('🍕 Buyurtma berish', config.miniAppUrl)]).resize()
  );
}

module.exports = { handleStart };
