const crypto = require('crypto');
const config = require('../config/default');

// Telegram Mini App initData'ni HMAC-SHA256 orqali tasdiqlaydi
// https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
function validateInitData(initData) {
  if (!initData || typeof initData !== 'string') return null;

  const urlParams = new URLSearchParams(initData);
  const hash = urlParams.get('hash');
  if (!hash) return null;

  urlParams.delete('hash');
  const dataCheckArr = [];
  for (const [key, value] of [...urlParams.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    dataCheckArr.push(`${key}=${value}`);
  }
  const dataCheckString = dataCheckArr.join('\n');

  const secretKey = crypto.createHmac('sha256', 'WebAppData').update(config.botToken).digest();
  const computedHash = crypto.createHmac('sha256', secretKey).update(dataCheckString).digest('hex');

  if (computedHash !== hash) return null;

  const userRaw = urlParams.get('user');
  if (!userRaw) return null;

  try {
    return JSON.parse(userRaw);
  } catch {
    return null;
  }
}

// Express middleware: header'dagi x-telegram-init-data'ni tekshiradi va (to'g'ri bo'lsa) req.telegramUser'ga yozadi
function telegramAuthMiddleware(req, res, next) {
  const initData = req.headers['x-telegram-init-data'];

  if (initData) {
    const telegramUser = validateInitData(initData);
    if (telegramUser) {
      req.telegramUser = telegramUser;
    }
  }

  next();
}

module.exports = { telegramAuthMiddleware, validateInitData };
