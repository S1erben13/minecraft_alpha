# Хиробрин — главная загадка Minecraft Alpha

[![Deploy static site](https://github.com/S1erben13/minecraft_alpha/actions/workflows/deploy.yml/badge.svg)](https://github.com/S1erben13/minecraft_alpha/actions/workflows/deploy.yml)

Одностраничный фанатский сайт об атмосфере Minecraft Alpha 1.0.16_02 и легенде о Хиробрине.
Учебный проект по дисциплине «Информатика» (ГУАП): лабораторная работа №4 — создание лендинга с помощью ИИ,
лабораторная работа №5 — организация репозитория в Git и публикация через GitHub Pages.

**Сайт:** https://s1erben13.github.io/minecraft_alpha/

## Структура

| Путь | Что лежит |
|------|-----------|
| `index.html` | итоговая страница: разметка и скрипт |
| `style.css` | стили сайта |
| `.github/workflows/deploy.yml` | workflow GitHub Actions: проверка и автодеплой на GitHub Pages |
| `.stylelintrc.json` | правила проверки CSS |
| `assets/` | изображения; `trace-*.webp` — собственные кадры раздела «Следы» |
| `tools/` | скрипт, которым отрендерены кадры 05–07 (Python, numpy, Pillow) |
| `archive/deepseek.html` | альтернативная версия страницы от DeepSeek (ЛР4) |
| `promts/` | промпты, использованные при генерации сайта |
| `idea.md` | замысел и структура проекта |

## Автодеплой (CI/CD)

При каждом push в `master` GitHub Actions запускает workflow `Deploy static site`:

1. **Проверка и сборка** — HTMLHint проверяет `index.html`, Stylelint — `style.css`, скрипт убеждается, что все локальные файлы, на которые ссылается страница, существуют; затем сайт собирается в папку `_site`.
2. **Публикация на GitHub Pages** — запускается, только если проверка прошла успешно.

Для pull request в `master` выполняется только проверка, без публикации. Бейдж вверху показывает статус последнего запуска.

## Ветки

- `master` — основная ветка, из неё публикуется сайт;
- `new-photos` — раздел «Следы» с тремя новыми кадрами;
- `fix-plus-button` — выравнивание значка «+» на кнопках увеличения;
- `readme` — этот файл с описанием проекта;
- `ci-checks` — проверки HTML/CSS перед деплоем и бейдж статуса сборки.

Неофициальный фанатский проект, не связан с Mojang Studios и Microsoft.
