const prisma = require('../database/connection');

async function findOrCreateUser({ telegramId, firstName, lastName, phone }) {
  const existing = await prisma.user.findUnique({ where: { telegramId: String(telegramId) } });

  if (existing) {
    if (phone && phone !== existing.phone) {
      return prisma.user.update({
        where: { id: existing.id },
        data: { phone },
      });
    }
    return existing;
  }

  return prisma.user.create({
    data: {
      telegramId: String(telegramId),
      firstName,
      lastName,
      phone,
    },
  });
}

async function getUserByTelegramId(telegramId) {
  return prisma.user.findUnique({ where: { telegramId: String(telegramId) } });
}

module.exports = {
  findOrCreateUser,
  getUserByTelegramId,
};
