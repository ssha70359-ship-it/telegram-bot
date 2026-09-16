const express = require('express');
const cors = require('cors');
const config = require('./config/default');

const bot = require('./routes/bot.routes');
const clientRoutes = require('./routes/client.routes');
const adminRoutes = require('./routes/admin.routes');

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api/client', clientRoutes);
app.use('/api/admin', adminRoutes);

app.get('/', (req, res) => {
  res.json({ status: 'ok', message: 'Pizza Delivery API ishlamoqda' });
});

app.listen(config.port, () => {
  console.log(`API server http://localhost:${config.port} manzilida ishga tushdi`);
});

let botRunning = false;

bot
  .launch()
  .then(() => {
    botRunning = true;
    console.log('Telegram bot ishga tushdi');
  })
  .catch((err) => console.error('Botni ishga tushirishda xatolik:', err.message));

function stopBot(signal) {
  if (botRunning) bot.stop(signal);
  process.exit(0);
}

process.once('SIGINT', () => stopBot('SIGINT'));
process.once('SIGTERM', () => stopBot('SIGTERM'));
