require('dotenv').config();

module.exports = {
  port: process.env.PORT || 4000,
  databaseUrl: process.env.DATABASE_URL,
  botToken: process.env.TELEGRAM_BOT_TOKEN,
  miniAppUrl: process.env.MINI_APP_URL,
};
