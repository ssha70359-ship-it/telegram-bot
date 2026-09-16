const Product = require('../models/Product');
const Order = require('../models/Order');
const User = require('../models/User');
const { notifyOrderAccepted } = require('../core/bot');

async function listProducts(req, res) {
  const products = await Product.getAllProducts();
  res.json(products);
}

async function getProduct(req, res) {
  const product = await Product.getProductById(req.params.id);
  if (!product) return res.status(404).json({ error: 'Mahsulot topilmadi' });
  res.json(product);
}

function resolveTelegramUser(req) {
  if (req.telegramUser) {
    return {
      telegramId: req.telegramUser.id,
      firstName: req.telegramUser.first_name,
      lastName: req.telegramUser.last_name,
    };
  }
  const bodyUser = req.body.telegramUser;
  if (bodyUser && bodyUser.id) {
    return {
      telegramId: bodyUser.id,
      firstName: bodyUser.first_name,
      lastName: bodyUser.last_name,
    };
  }
  return null;
}

async function createOrder(req, res) {
  const telegramUser = resolveTelegramUser(req);
  if (!telegramUser) {
    return res.status(400).json({ error: 'Telegram foydalanuvchisi aniqlanmadi' });
  }

  const { items, totalPrice, location, phone } = req.body;
  if (!items || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: "Savatcha bo'sh" });
  }
  if (!totalPrice) {
    return res.status(400).json({ error: "Jami summa ko'rsatilmagan" });
  }

  const user = await User.findOrCreateUser({ ...telegramUser, phone });

  const order = await Order.createOrder({
    userId: user.id,
    items,
    totalPrice,
    location,
  });

  try {
    await notifyOrderAccepted(user.telegramId);
  } catch (err) {
    console.error("Telegram xabar yuborishda xatolik:", err.message);
  }

  res.status(201).json(order);
}

async function myOrders(req, res) {
  const telegramUser = resolveTelegramUser(req);
  if (!telegramUser) {
    return res.status(400).json({ error: 'Telegram foydalanuvchisi aniqlanmadi' });
  }

  const user = await User.getUserByTelegramId(telegramUser.telegramId);
  if (!user) return res.json([]);

  const orders = await Order.getOrdersByUserId(user.id);
  res.json(orders);
}

async function syncUser(req, res) {
  const telegramUser = resolveTelegramUser(req);
  if (!telegramUser) {
    return res.status(400).json({ error: 'Telegram foydalanuvchisi aniqlanmadi' });
  }

  const { phone } = req.body;
  const user = await User.findOrCreateUser({ ...telegramUser, phone });
  res.json(user);
}

module.exports = { listProducts, getProduct, createOrder, myOrders, syncUser };
