const prisma = require('../database/connection');

async function getAllProducts() {
  return prisma.product.findMany({ orderBy: { id: 'asc' } });
}

async function getProductById(id) {
  return prisma.product.findUnique({ where: { id: Number(id) } });
}

async function createProduct(data) {
  return prisma.product.create({
    data: {
      name: data.name,
      description: data.description,
      imageUrl: data.imageUrl,
      oldPrice: data.oldPrice ? Number(data.oldPrice) : null,
      newPrice: Number(data.newPrice),
      category: data.category,
    },
  });
}

async function updateProduct(id, data) {
  return prisma.product.update({
    where: { id: Number(id) },
    data: {
      name: data.name,
      description: data.description,
      imageUrl: data.imageUrl,
      oldPrice: data.oldPrice ? Number(data.oldPrice) : null,
      newPrice: Number(data.newPrice),
      category: data.category,
    },
  });
}

async function deleteProduct(id) {
  return prisma.product.delete({ where: { id: Number(id) } });
}

module.exports = {
  getAllProducts,
  getProductById,
  createProduct,
  updateProduct,
  deleteProduct,
};
