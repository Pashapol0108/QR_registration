# QR-регистрация

Инструкция по запуску проекта на Python с Flask и зависимостями.

---

## 1. Установка Python

Проект поддерживает Python 3.9–3.11.  
Скачать можно с [официального сайта Python](https://www.python.org/downloads/).

> pip обычно устанавливается вместе с Python.

---

## 2. Установка зависимостей и запуск проекта

### Windows

1. Перейти в папку проекта:

```cmd
cd C:\Users\p.polyakov\Desktop\qr
```

2. Создать виртуальное окружение:

```cmd
python -m venv .venv
```

3. Активировать виртуальное окружение:

```cmd
.venv\Scripts\activate.bat
```

4. Установить зависимости:

```cmd
python -m pip install -r requirements.txt
```

> При необходимости обновить pip:
>
> ```cmd
> python -m pip install --upgrade pip
> ```

5. Запустить приложение:

```cmd
python app.py
```

Приложение будет доступно по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### macOS / Linux

1. Перейти в папку проекта:

```bash
cd ~/Desktop/qr
```

2. Создать виртуальное окружение:

```bash
python3 -m venv venv
```

3. Активировать виртуальное окружение:

```bash
source venv/bin/activate
```

4. Установить зависимости:

```bash
pip install -r requirements.txt
```

> При необходимости обновить pip:
>
> ```bash
> pip install --upgrade pip
> ```

5. Запустить приложение:

```bash
python app.py
```

Приложение будет доступно по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

