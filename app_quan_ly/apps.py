from django.apps import AppConfig

class AppQuanLyConfig(AppConfig):  # ← Sửa tên class này
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_quan_ly'  # ← Đảm bảo đúng tên app
    
    def ready(self):
        """Import signals khi app khởi động"""
        import app_quan_ly.signals