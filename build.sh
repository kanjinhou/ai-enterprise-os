#!/usr/bin/env bash
# 如果任何命令失败，就停止执行
set -o errexit

# 1. 安装依赖库
pip install -r requirements.txt

# 2. 收集静态文件 (CSS/JS等)
python manage.py collectstatic --no-input

# 3. 核心步骤：自动执行数据库迁移 (这就相当于你手动敲 migrate)
python manage.py migrate

# 4. 超级大招：自动创建一个管理员账号 (如果不存在的话)
# 账号: admin
# 密码: admin123 (进去后记得改！)
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"