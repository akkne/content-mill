import type { Translate } from "./interface-language";

export type VideoFailure = {
  stage: string;
  reason: string;
  http_status?: number;
  provider_code?: string;
};

export function videoFailureMessage(t: Translate, reason: string) {
  const messages: Record<string, string> = {
    heygen_key: t("Для синхронизации губ добавьте HEYGEN_API_KEY на сервере.","Set HEYGEN_API_KEY on the server for lip sync."),
    speech_failed: t("Сервис не выдал озвучку реплики.","The speech service did not deliver the line."),
    speech_too_long: t("Реплика не помещается в интервал. Создайте вариант с более короткой репликой.","The line exceeds its time slot. Create a variation with a shorter line."),
    speech_unavailable: t("Для голосов персонажей добавьте LUMEAN_API_KEY.","Set LUMEAN_API_KEY for character voices."),
    lipsync_failed: t("HeyGen не смог синхронизировать сцену.","HeyGen could not synchronize this scene."),
    short_dub: t("Синхронизированный клип слишком короткий.","The synchronized clip is too short."),
    clip_rejected: t("Провайдер отклонил клип.", "The provider rejected this clip."),
    frame_rejected: t("Провайдер отклонил кадр.", "The provider rejected the frame."),
    legacy_operation: t("Заказ относится к прежнему провайдеру.", "This order belongs to the previous provider."),
    polza_limit: t("Достигнут лимит Polza AI. Повторите позже.", "Polza AI rate limit reached. Try again later."),
    polza_key: t("На сервере нужен POLZA_API_KEY.", "Set POLZA_API_KEY on the server."),
    polza_access: t("Проверьте доступ ключа Polza AI к моделям.", "Check the Polza AI key’s model access."),
    polza_balance: t("Недостаточно средств на Polza AI.", "Insufficient Polza AI balance."),
    codex_unavailable: t("Проверьте вход Codex на сервере.", "Check the server’s Codex login."),
    interrupted: t("Обработка прервалась. Проверьте списания перед повтором.", "Processing was interrupted. Check charges before retrying."),

    missing_source: t("Версия исходного материала больше недоступна. Проверьте файлы проекта.", "A source version is no longer available. Check the project files."),
    fal_key: t("Проверьте подключение fal на сервере.", "Check the fal connection on the server."),
    fal_access: t("Проверьте права аккаунта fal.", "Check the fal account permissions."),
    fal_balance: t("Недостаточно средств на счёте fal.", "Insufficient fal credit."),
    public_figure: t("Модерация провайдера обнаружила публичную личность во входных материалах. Для нового ролика выберите другого персонажа и подходящие референсы.", "The provider flagged a public figure in the input. Choose a different character and matching references for a new video."),
    moderation: t("Материалы отклонены модерацией провайдера. Пересмотрите бриф и референсы перед созданием нового ролика.", "The provider blocked the content. Review the brief and references before creating a new video."),
    authentication: t("Сервис отклонил учётные данные. Попросите администратора проверить подключение.", "The service rejected the credentials. Ask an administrator to check the connection."),
    permission: t("Сервис запретил доступ. Администратору нужно проверить права аккаунта.", "The service denied access. Ask an administrator to check the account permissions."),
    balance: t("Средств или квоты для задания недостаточно. Проверьте баланс аккаунта провайдера.", "There is insufficient credit or quota. Check the provider account balance."),
    rate_limit: t("Сервис ограничил частоту или число одновременных запросов. Повторите позже.", "The service limited the request rate or concurrency. Try again later."),
    invalid_input: t("Сервис отклонил параметры запроса. Проверьте материалы и настройки генерации.", "The service rejected the request parameters. Check the materials and generation settings."),
    too_large: t("Данные превышают допустимый размер. Для нового ролика уменьшите объём материалов.", "The data exceeds the size limit. Use smaller inputs for a new video."),
    unsupported_format: t("Сервис не поддерживает формат входного файла. Проверьте выбранные материалы.", "The input format is unsupported. Check the selected materials."),
    not_found: t("Сервис не нашёл запрошенный ресурс. Проверьте доступность модели, файла или заказа.", "The service could not find the requested resource. Check the model, file or order."),
    expired: t("Срок доступа к ресурсу истёк. Проверьте доступность результата у провайдера.", "Access to the resource expired. Check result availability with the provider."),
    conflict: t("Сервис сообщил о конфликте запросов. Проверьте состояние заказа перед повтором.", "The service reported a request conflict. Check the order before retrying."),
    timeout: t("Время ожидания истекло. Если запрос уже был отправлен, проверьте его состояние у провайдера.", "The operation timed out. If a request was submitted, check its status with the provider."),
    network: t("Не удалось завершить обмен с сервисом. Проверьте соединение и состояние заказа.", "Communication with the service failed. Check connectivity and the order status."),
    provider_down: t("Сервис сообщил о внутреннем сбое. Повторите позже.", "The service reported an internal failure. Try again later."),
    cancelled: t("Провайдер отменил заказ.", "The provider cancelled the order."),
    http_error: t("Сервис вернул неожиданный HTTP-ответ. Передайте код администратору.", "The service returned an unexpected HTTP response. Give the code to an administrator."),
    invalid_response: t("Ответ или файл сервиса имеет неожиданный формат. Администратору нужно проверить интеграцию.", "The service returned an unexpected response or file format. Ask an administrator to check the integration."),
    storage: t("Не удалось прочитать или сохранить файл в хранилище проекта. Проверьте доступность хранилища.", "A project file could not be read or saved. Check that storage is available."),
    invalid_frame: t("Полученное изображение не удалось прочитать как PNG.", "The generated image could not be read as a PNG."),
    invalid_clip: t("Полученный клип не прошёл проверку дорожек или длительности.", "The generated clip failed track or duration checks."),
    invalid_script: t("Данные сценария не прошли проверку формата.", "The script data failed format validation."),
    invalid_storyboard: t("Данные раскадровки не прошли проверку. Проверьте сцены, реплики и материалы.", "Storyboard validation failed. Check the scenes, dialogue and materials."),
    invalid_edit: t("Данные для монтажа не прошли проверку. Проверьте исходники, склейки и таймкоды.", "Edit validation failed. Check the clips, cuts and timecodes."),
    render_failed: t("Не удалось собрать итоговый MP4 по монтажному листу.", "The final MP4 could not be rendered from the edit decisions."),
    media_processing: t("Сбой обработки аудио или видео. Проверьте исходные дорожки.", "Media processing failed. Check the source tracks."),
    audio_failed: t("Не удалось совместить голосовую дорожку со сценой.", "The speech track could not be combined with the scene."),
    lipsync_input: t("Файл для синхронизации губ превышает 50 МБ.", "The lip sync input exceeds 50 MB."),
    model_failed: t("Текстовая модель завершила работу с ошибкой. Проверьте подключение и доступную квоту.", "The text model failed. Check the connection and available quota."),
  };
  return messages[reason] ?? t("Не удалось завершить этап. Если ошибка повторится, передайте администратору код и название этапа.", "The stage could not finish. If this happens again, give the administrator the code and stage name.");
}

export function failureCode(failure: VideoFailure) {
  return [failure.provider_code ?? failure.reason, failure.http_status && `HTTP ${failure.http_status}`].filter(Boolean).join(" · ");
}
