Как запустить:
1. Склонировать репозиторий командой в терминале 
   
   ```git clone https://github.com/elizabethuglova/uglova_webAI.git```

   либо можно скачать zip архив проекта
2. Перейти в папку проекта 
3. Создать виртуальное окружение 
   
   ```python -m venv venv```
4. Активировать виртуальное окружение 
   
   Windows:
   
   ```venv\Scripts\activate```
   
   Linux/macOS:
   
   ```source venv/bin/activate```
5. Установить зависимости 

   ```pip install -r requirements.txt```
6. Можно запустить тестирование, при пустой БД

   ```python -m unittest test_app.py```
8. Запустить приложение
   
   ```python main.py```
9. Перейти на сайт
   http://127.0.0.1:8080/

10. Можно выполнить тестирование с заполненной БД, для начала остановить выполнение приложения, затем выполнить команду:

     ```python -m unittest test_app.py```
