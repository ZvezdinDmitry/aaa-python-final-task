# Telegram бот для игры в крестики-нолики
Клонирование репозитория:
```bash
git clone git@github.com:ZvezdinDmitry/aaa-python-final-task.git
```
Запуск:
```bash
export TG_TOKEN=YOUR_TOKEN
pip install uv
uv sync
uv run main.py
```
Оценить покрытие тестами:
```bash
uv run pytest -v tests.py --cov=main
```
