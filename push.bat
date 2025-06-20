@echo off
cd /d %~dp0

echo Добавление всех файлов...
git add .

echo Введите комментарий к коммиту:
set /p msg="Комментарий: "

git commit -m "%msg%"
git push

echo ============================
echo ✅ Успешно отправлено на GitHub!
pause
