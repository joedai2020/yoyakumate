from pathlib import Path

# プロジェクトのベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent

# 本番環境ではこのキーを秘密にしてください
SECRET_KEY = 'django-insecure-4-dw)p!vmzj-4zrtpl=7q-bl3^==k)$do9=71-q6ma*o$e0ffp'

# デバッグモード（本番環境では必ずFalseに設定）
DEBUG = True

# 許可するホスト名（本番では設定が必要）
ALLOWED_HOSTS = []

# アプリケーション定義
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reservations',  # ← 予約管理アプリを追加
]

# ミドルウェア定義
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL設定のルート
ROOT_URLCONF = 'yoyakumate.urls'

# テンプレートエンジンの設定
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # テンプレートのカスタムパスがあればここに追加
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGIアプリケーション
WSGI_APPLICATION = 'yoyakumate.wsgi.application'

# データベース設定（SQLite）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# パスワードバリデーター（セキュリティ向上のため）
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 国際化と言語設定
LANGUAGE_CODE = 'ja'  # 日本語に変更

# タイムゾーン設定
TIME_ZONE = 'Asia/Tokyo'  # 日本時間に変更

USE_I18N = True  # 国際化対応
USE_TZ = True    # タイムゾーンのサポートを有効化

# 静的ファイルのURL（CSSや画像など）
STATIC_URL = 'static/'

# デフォルトの主キーの型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# カスタムユーザーモデルの指定
AUTH_USER_MODEL = 'reservations.CustomUser'

LOGIN_URL = '/login/'
