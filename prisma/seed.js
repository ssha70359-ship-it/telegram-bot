const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

const products = [
  {
    name: 'Margarita',
    description: 'Mozzarella pishloq, pomidor sousi va rayhon barglari bilan klassik pizza.',
    imageUrl: 'https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=800',
    oldPrice: 65000,
    newPrice: 49000,
    category: 'Klassik',
  },
  {
    name: 'Peperoni',
    description: 'Achchiq peperoni kolbasa va mol-mol mozzarella bilan sevimli pizza.',
    imageUrl: 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=800',
    oldPrice: 75000,
    newPrice: 59000,
    category: 'Klassik',
  },
  {
    name: 'Qazi pizza',
    description: "Milliy qazi go'shti, piyoz va maxsus sous bilan tayyorlangan noyob pizza.",
    imageUrl: 'https://images.unsplash.com/photo-1601924582970-9238bcb495d9?w=800',
    oldPrice: 95000,
    newPrice: 79000,
    category: "Go'shtli",
  },
  {
    name: 'Pishloqli',
    description: "To'rt xil pishloq - mozzarella, chedder, parmezan va gorgonzola bilan.",
    imageUrl: 'https://images.unsplash.com/photo-1601924928290-2ecd0edac30d?w=800',
    oldPrice: 80000,
    newPrice: 65000,
    category: 'Pishloqli',
  },
];

async function main() {
  console.log('Seed boshlandi...');

  for (const product of products) {
    const existing = await prisma.product.findFirst({ where: { name: product.name } });
    if (!existing) {
      await prisma.product.create({ data: product });
      console.log(`+ ${product.name} qo'shildi`);
    } else {
      console.log(`- ${product.name} allaqachon mavjud, o'tkazib yuborildi`);
    }
  }

  console.log('Seed yakunlandi.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
