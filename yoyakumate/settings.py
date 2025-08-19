from pathlib import Path
import os

# プロジェクトのベースディレクトリを定義（settings.py の2階層上のディレクトリ）
BASE_DIR = Path(__file__).resolve().parent.parent

# Djangoの秘密鍵（本番環境では絶対に外部に漏らさないこと）
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-仮のキー')

# デバッグモードの設定（開発中はTrue、本番ではFalseにする）
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'False'

# 許可するホスト名のリスト（テスト環境ではローカルホストを許可）
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'https://yoyakumate-a7fzbyf9c9acdnes.japanwest-01.azurewebsites.net',
]

# インストール済みアプリケーションのリスト
INSTALLED_APPS = [
    'django.contrib.admin',           # 管理サイト
    'django.contrib.auth',            # 認証システム
    'django.contrib.contenttypes',    # コンテンツタイプフレームワーク
    'django.contrib.sessions',        # セッション管理
    'django.contrib.messages',        # メッセージフレームワーク
    'django.contrib.staticfiles',     # 静的ファイル管理
    'reservations',                   # 予約管理用アプリ
    'crispy_forms',                   # フォームのスタイリング用
    'crispy_bootstrap5',              # Bootstrap5 用 Crispy Forms テンプレート
]

# Crispy Formsのテンプレートパック設定
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ミドルウェアの定義（リクエスト・レスポンス処理の中間処理）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',        # セキュリティ関連の処理
    'django.contrib.sessions.middleware.SessionMiddleware', # セッション管理
    'django.middleware.common.CommonMiddleware',            # 共通処理（リクエストの正規化など）
    'yoyakumate.middleware.log_exception.ExceptionLoggingMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',            # CSRF攻撃防止
    'django.contrib.auth.middleware.AuthenticationMiddleware', # 認証情報管理
    'django.contrib.messages.middleware.MessageMiddleware', # メッセージ管理
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # クリックジャッキング対策
]

# URL設定のルートモジュール
ROOT_URLCONF = 'yoyakumate.urls'

# テンプレートエンジンの設定
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Django標準テンプレートエンジン
        'DIRS': [BASE_DIR / 'templates'],  # カスタムテンプレート用ディレクトリ
        'APP_DIRS': True,                  # アプリケーションごとのtemplatesフォルダを自動検索
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',   # リクエストをテンプレートに渡す
                'django.contrib.auth.context_processors.auth',  # 認証情報をテンプレートに渡す
                'django.contrib.messages.context_processors.messages',  # メッセージ情報を渡す
            ],
        },
    },
]

# WSGIアプリケーションの指定
WSGI_APPLICATION = 'yoyakumate.wsgi.application'

# データベース設定（開発段階ではSQLiteを利用）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # SQLiteデータベースエンジン
        'NAME': '/home/site/db.sqlite3',
    }
}

# パスワードバリデーションの設定（セキュリティ強化）
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},  # 類似した属性はNG
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},             # 最小長さ制限
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},            # よくあるパスワード不可
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},           # 数字のみ不可
]

# 言語コード設定（日本語）
LANGUAGE_CODE = 'ja'

# タイムゾーン設定（日本時間）
TIME_ZONE = 'Asia/Tokyo'

# 国際化対応を有効にするか
USE_I18N = True

# タイムゾーン対応を有効にするか
USE_TZ = True

# 静的ファイルのURL（Webページで使うCSSやJS、画像のパスの基準）
STATIC_URL = '/static/'

# 開発用に静的ファイルをまとめるフォルダを指定（存在すれば）
STATICFILES_DIRS = [BASE_DIR / "staticfiles"]

# モデルの主キーのデフォルト設定
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# カスタムユーザーモデルを使用する指定
AUTH_USER_MODEL = 'reservations.CustomUser'

# ログイン画面のURL（認証が必要なページアクセス時のリダイレクト先）
LOGIN_URL = '/login/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 既存のロガーを無効にしない
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',  # 詳細なログ形式
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',  # 簡易ログ形式
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',  # コンソール出力用
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',  # 日次ローテーションファイル出力
            'filename': '/home/LogFiles/django.log',  # ログファイルの保存先
            'when': 'D',               # 日単位でローテーション
            'interval': 1,             # 毎日1回ローテーション
            'backupCount': 7,          # 最大7日分のログを保持
            'encoding': 'utf-8',       # 文字化け防止（日本語対応）
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],  # Django関連のログを出力
            'level': 'INFO',                  # INFO以上のログを記録
            'propagate': True,
        },
        'reservations': {
            'handlers': ['console', 'file'],  # reservationsアプリ専用のログ
            'level': 'DEBUG',                 # DEBUG以上のログを記録
            'propagate': False,
        },
    },
}

# セキュリティ強化設定（本番向けに）
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
