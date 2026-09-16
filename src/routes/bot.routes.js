const { bot } = require('../core/bot');
const botController = require('../controllers/botController');

bot.start(botController.handleStart);

module.exports = bot;
