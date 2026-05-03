"""
Başlangıç verisi: admin + demo kullanıcı + abonelik paketleri + demo şirket verisi.
Çalıştır: python -m scripts.seed
"""
import sys
import os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole, SubscriptionPackage, Company,
    CompanyBank, Collection, CompanyProject, Investment,
)
from app.models.extended import CollectionType, ProjectStatus, InvestmentStatus
from app.models.company import ContractType
from app.core.security import get_password_hash


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ── Admin kullanıcı ──────────────────────────────────────────────
        admin = db.query(User).filter(User.email == "admin@platform.com").first()
        if not admin:
            admin = User(
                email="admin@platform.com",
                hashed_password=get_password_hash("Admin1234!"),
                full_name="Platform Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            db.flush()
            print("Admin kullanıcı oluşturuldu: admin@platform.com / Admin1234!")

        # ── Demo kullanıcı ───────────────────────────────────────────────
        demo_user = db.query(User).filter(User.email == "demo@platform.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@platform.com",
                hashed_password=get_password_hash("Demo1234!"),
                full_name="Demo Kullanıcı",
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
            )
            db.add(demo_user)
            db.flush()
            print("Demo kullanıcı oluşturuldu: demo@platform.com / Demo1234!")

        # ── Abonelik paketleri ───────────────────────────────────────────
        packages = [
            dict(
                name="Temel Analiz",
                description="Küçük ölçekli firmalar için temel AI analiz paketi.",
                price=0.00,
                duration_days=30,
                max_companies=3,
                max_reports_per_month=10,
                max_ai_calls_per_month=20,
                features={"pptx_export": True, "ai_analysis": True, "ocr": False},
            ),
            dict(
                name="Uzman Görüşü",
                description="Uzman tarafından yazılan yorumlu rapor desteği.",
                price=0.00,
                duration_days=30,
                max_companies=15,
                max_reports_per_month=50,
                max_ai_calls_per_month=100,
                features={"pptx_export": True, "ai_analysis": True, "ocr": True, "expert_review": True},
            ),
            dict(
                name="Premium Bundle",
                description="AI Analiz + Uzman Görüşü + Ön Sunum — tam paket.",
                price=0.00,
                duration_days=30,
                max_companies=999,
                max_reports_per_month=999,
                max_ai_calls_per_month=999,
                features={"pptx_export": True, "ai_analysis": True, "ocr": True,
                          "expert_review": True, "priority_support": True},
            ),
        ]

        for pkg_data in packages:
            if not db.query(SubscriptionPackage).filter(SubscriptionPackage.name == pkg_data["name"]).first():
                db.add(SubscriptionPackage(**pkg_data))
                print(f"Paket oluşturuldu: {pkg_data['name']}")

        db.flush()

        # ── Demo şirket verisi (admin kullanıcıya bağlı) ─────────────────
        owner_id = admin.id if admin.id else 1

        if not db.query(Company).filter(Company.name == "Alfa Teknoloji A.Ş.").first():
            alfa = Company(
                owner_id=owner_id,
                name="Alfa Teknoloji A.Ş.",
                tax_id="1234567890",
                trade_registry_no="TR-İST-2015-001234",
                sector="Teknoloji",
                description="Yazılım geliştirme ve dijital dönüşüm danışmanlığı.",
                founding_date=date(2015, 3, 15),
                authorized_person_name="Mehmet Yılmaz",
                contact_phone="+90 212 555 0101",
                contact_email="info@alfateknoloji.com",
                address="Maslak Mah. Büyükdere Cad. No:255 Sarıyer/İstanbul",
                annual_revenue_estimate=15000000,
                annual_revenue_actual=14200000,
                contract_amount=120000,
                contract_start=date(2024, 1, 1),
                contract_end=date(2024, 12, 31),
                contract_type=ContractType.ANALYSIS,
            )
            db.add(alfa)
            db.flush()

            # Bankalar
            for bank in [
                CompanyBank(company_id=alfa.id, bank_name="Ziraat Bankası",
                            account_no="TR12 0001 0000 0000 0012 3456 78",
                            currency="TRY", balance=2500000, credit_limit=5000000, credit_usage=1800000),
                CompanyBank(company_id=alfa.id, bank_name="İş Bankası",
                            account_no="TR34 0006 4000 0011 1000 0000 01",
                            currency="TRY", balance=850000, credit_limit=2000000, credit_usage=400000),
                CompanyBank(company_id=alfa.id, bank_name="Garanti BBVA",
                            account_no="TR76 0006 2000 0010 0000 0001 23",
                            currency="USD", balance=120000, credit_limit=500000, credit_usage=0),
            ]:
                db.add(bank)

            # Tahsilatlar
            for coll in [
                Collection(company_id=alfa.id, collection_type=CollectionType.PENDING,
                           amount=450000, counterparty="Beta İnşaat Ltd.", due_date=date(2024, 6, 30), is_overdue=True,
                           description="2024 Q1 danışmanlık ücreti"),
                Collection(company_id=alfa.id, collection_type=CollectionType.PENDING,
                           amount=220000, counterparty="Gama Lojistik A.Ş.", due_date=date(2024, 8, 15),
                           description="Yazılım lisans bedeli"),
                Collection(company_id=alfa.id, collection_type=CollectionType.PENDING,
                           amount=180000, counterparty="Delta Enerji A.Ş.", due_date=date(2024, 9, 1),
                           description="Sistem entegrasyon projesi"),
                Collection(company_id=alfa.id, collection_type=CollectionType.COMPLETED,
                           amount=380000, counterparty="Epsilon Holding", collection_date=date(2024, 3, 10),
                           description="2023 yıl sonu raporu"),
                Collection(company_id=alfa.id, collection_type=CollectionType.COMPLETED,
                           amount=290000, counterparty="Zeta Perakende", collection_date=date(2024, 4, 5),
                           description="Q4 analiz paketi"),
            ]:
                db.add(coll)

            # Projeler
            for proj in [
                CompanyProject(company_id=alfa.id, name="ERP Modernizasyon Projesi",
                               status=ProjectStatus.ONGOING, client_name="Beta İnşaat Ltd.",
                               start_date=date(2024, 1, 15), value=850000,
                               description="SAP S/4HANA geçiş projesi"),
                CompanyProject(company_id=alfa.id, name="Mobil Uygulama Geliştirme",
                               status=ProjectStatus.ONGOING, client_name="Gama Lojistik A.Ş.",
                               start_date=date(2024, 3, 1), value=320000,
                               description="iOS & Android lojistik takip uygulaması"),
                CompanyProject(company_id=alfa.id, name="Bulut Altyapı Geçişi",
                               status=ProjectStatus.ONGOING, client_name="Delta Enerji A.Ş.",
                               start_date=date(2024, 2, 1), value=540000,
                               description="AWS migration projesi"),
                CompanyProject(company_id=alfa.id, name="Siber Güvenlik Denetimi",
                               status=ProjectStatus.COMPLETED, client_name="Epsilon Holding",
                               start_date=date(2023, 9, 1), end_date=date(2023, 12, 31), value=250000,
                               description="ISO 27001 hazırlık danışmanlığı"),
                CompanyProject(company_id=alfa.id, name="Veri Ambarı Kurulumu",
                               status=ProjectStatus.COMPLETED, client_name="Zeta Perakende",
                               start_date=date(2023, 6, 1), end_date=date(2023, 11, 30), value=410000,
                               description="Snowflake tabanlı BI altyapısı"),
            ]:
                db.add(proj)

            # Yatırımlar
            for inv in [
                Investment(company_id=alfa.id, name="Borsa Portföyü",
                           investment_type="Hisse Senedi", sector="Finans",
                           geography="Türkiye", status=InvestmentStatus.ACTIVE,
                           purchase_value=500000, current_value=680000, planned_return_pct="15%",
                           risk_score=65, purchase_date=date(2022, 6, 1)),
                Investment(company_id=alfa.id, name="Gayrimenkul – Maslak Ofis",
                           investment_type="Gayrimenkul", sector="Emlak",
                           geography="İstanbul", status=InvestmentStatus.ACTIVE,
                           purchase_value=3200000, current_value=4100000, planned_return_pct="8%",
                           risk_score=30, purchase_date=date(2020, 3, 15)),
                Investment(company_id=alfa.id, name="StartUp Yatırımı – FinTech",
                           investment_type="Girişim Sermayesi", sector="FinTech",
                           geography="Türkiye", status=InvestmentStatus.ACTIVE,
                           purchase_value=250000, current_value=410000, planned_return_pct="40%",
                           risk_score=80, purchase_date=date(2023, 1, 10)),
                Investment(company_id=alfa.id, name="Hazine Bonosu Portföyü",
                           investment_type="Tahvil/Bono", sector="Kamu",
                           geography="Türkiye", status=InvestmentStatus.PLANNED,
                           purchase_value=1000000, current_value=1000000, planned_return_pct="28%",
                           risk_score=15),
            ]:
                db.add(inv)

            print("Demo şirket verisi oluşturuldu: Alfa Teknoloji A.Ş.")

        db.commit()
        print("\nSeed tamamlandı.")
        print("Admin: admin@platform.com / Admin1234!")
        print("Demo:  demo@platform.com  / Demo1234!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
