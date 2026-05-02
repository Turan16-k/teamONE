"""
Başlangıç verisi: admin kullanıcı + abonelik paketleri.
Çalıştır: python -m scripts.seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, User, UserRole, SubscriptionPackage
from app.core.security import get_password_hash


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Admin kullanıcı
        if not db.query(User).filter(User.email == "admin@platform.com").first():
            admin = User(
                email="admin@platform.com",
                hashed_password=get_password_hash("Admin1234!"),
                full_name="Platform Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            print("Admin kullanıcı oluşturuldu: admin@platform.com / Admin1234!")

        # Abonelik paketleri
        packages = [
            dict(
                name="Başlangıç",
                description="Küçük ölçekli firmalar için temel analiz paketi.",
                price=299.00,
                duration_days=30,
                max_companies=3,
                max_reports_per_month=10,
                max_ai_calls_per_month=20,
                features={"pptx_export": True, "ai_analysis": True, "ocr": False},
            ),
            dict(
                name="Profesyonel",
                description="Büyüyen işletmeler için tam OCR ve AI analizi.",
                price=799.00,
                duration_days=30,
                max_companies=15,
                max_reports_per_month=50,
                max_ai_calls_per_month=100,
                features={"pptx_export": True, "ai_analysis": True, "ocr": True},
            ),
            dict(
                name="Kurumsal",
                description="Sınırsız kullanım ve öncelikli destek.",
                price=1999.00,
                duration_days=30,
                max_companies=999,
                max_reports_per_month=999,
                max_ai_calls_per_month=999,
                features={"pptx_export": True, "ai_analysis": True, "ocr": True, "priority_support": True},
            ),
        ]

        for pkg_data in packages:
            if not db.query(SubscriptionPackage).filter(SubscriptionPackage.name == pkg_data["name"]).first():
                db.add(SubscriptionPackage(**pkg_data))
                print(f"Paket oluşturuldu: {pkg_data['name']}")

        db.commit()
        print("\nSeed tamamlandı.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
