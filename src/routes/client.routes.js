const { Router } = require('express');
const cartController = require('../controllers/cartController');
const { telegramAuthMiddleware } = require('../middlewares/auth.middleware');

const router = Router();

router.use(telegramAuthMiddleware);

router.get('/products', cartController.listProducts);
router.get('/products/:id', cartController.getProduct);
router.post('/user/sync', cartController.syncUser);
router.get('/orders', cartController.myOrders);
router.post('/orders', cartController.createOrder);

module.exports = router;
