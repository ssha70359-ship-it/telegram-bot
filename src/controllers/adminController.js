const Product = require('../models/Product');
const Order = require('../models/Order');

async function listOrders(req, res) {
  const orders = await Order.getAllOrders();
  res.json(orders);
}

async function updateOrderStatus(req, res) {
  const { status } = req.body;
  if (!status) return res.status(400).json({ error: "Holat ko'rsatilmagan" });
  const order = await Order.updateOrderStatus(req.params.id, status);
  res.json(order);
}

async function listProducts(req, res) {
  const products = await Product.getAllProducts();
  res.json(products);
}

async function createProduct(req, res) {
  const { name, newPrice, category } = req.body;
  if (!name || !newPrice || !category) {
    return res.status(400).json({ error: "Nomi, narxi va kategoriyasi majburiy" });
  }
  const product = await Product.createProduct(req.body);
  res.status(201).json(product);
}

async function updateProduct(req, res) {
  const product = await Product.updateProduct(req.params.id, req.body);
  res.json(product);
}

async function deleteProduct(req, res) {
  await Product.deleteProduct(req.params.id);
  res.status(204).send();
}

module.exports = {
  listOrders,
  updateOrderStatus,
  listProducts,
  createProduct,
  updateProduct,
  deleteProduct,
};
