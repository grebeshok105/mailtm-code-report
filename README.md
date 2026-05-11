# mailtm-code-report

Небольшой Python-инструмент для проверки нескольких уже зарегистрированных mail.tm аккаунтов и извлечения кодов подтверждения из входящих писем.

Да, это возможно через официальный mail.tm API:

1. `POST /token` с `address` + `password` получает Bearer token.
2. `GET /messages` читает список писем аккаунта.
3. `GET /messages/{id}` забирает тело письма.
4. Локальный анализатор ищет OTP/verification-коды и возвращает результат.

Проект также содержит распакованные Devin skills в `.devin/skills/`.

## Быстрый старт

Требуется Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp accounts.example.txt accounts.txt
```

Заполните `accounts.txt`, по одному аккаунту на строку:

```text
email@domain.mail.tm:password
second@domain.mail.tm:another-password
```

Пароль может содержать `:`, деление идёт по первому двоеточию.

Также поддерживается JSON-формат. Если удобнее, создайте `accounts.json`:

```json
{
  "accounts": [
    {
      "address": "example@domain.mail.tm",
      "password": "password-from-mailtm"
    }
  ]
}
```

`accounts.txt` и `accounts.json` добавлены в `.gitignore`, потому что содержат пароли.

## CLI-анализ

```bash
mailtm-code-report scan --accounts accounts.txt
```

Только последние N писем каждого аккаунта:

```bash
mailtm-code-report scan --limit 5
```

Своя регулярка для кода:

```bash
mailtm-code-report scan --code-regex '(?<!\d)\d{6}(?!\d)'
```

## Веб-интерфейс с кнопкой

```bash
mailtm-code-report server --accounts accounts.txt --host 127.0.0.1 --port 8000
```

Откройте `http://127.0.0.1:8000` и нажмите **Анализировать аккаунты**.

## Отправка найденных кодов

По умолчанию результаты выводятся в CLI/веб-интерфейс. Если нужно “присылать” найденные коды в Telegram, задайте:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
mailtm-code-report scan --notify telegram
```

Или через произвольный webhook:

```bash
export CODE_REPORT_WEBHOOK_URL="https://example.com/webhook"
mailtm-code-report scan --notify webhook
```

Webhook получает JSON:

```json
{
  "account": "example@domain.mail.tm",
  "message_id": "...",
  "from_address": "sender@example.com",
  "subject": "Verification code",
  "codes": ["123456"]
}
```

## Ограничения mail.tm

- Общий лимит API — около 8 запросов в секунду с IP.
- Аккаунт должен уже существовать, а пароль должен быть известен.
- Используйте только легальные сценарии и соблюдайте правила mail.tm: https://docs.mail.tm/

## Проверки

```bash
python -m compileall src tests
python -m unittest discover -s tests
```
