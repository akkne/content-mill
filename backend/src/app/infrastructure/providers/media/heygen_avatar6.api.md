# HeyGen Avatar 6 Turbo

POST /v3/assets загружает PNG и WAV. POST /v3/models/avatars принимает model=heygen-avatar-6-turbo, reference_images с одним asset_id, audio с asset_id и resolution=1080p. Ответ 202 содержит data.video_id. GET /v3/models/videos/{id} возвращает статус, а после завершения data.video_url. Перед повтором с неизвестным результатом требуется проверить предыдущий заказ. Живой заказ проверяется с ключом пользователя.

[Генерация](https://developers.heygen.com/reference/create-avatar-6-video) · [Получение результата](https://developers.heygen.com/reference/get-heygen-video).
