"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "user", "analyst", name="userrole"), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])

    # companies
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tax_id", sa.String(50), unique=True),
        sa.Column("sector", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_owner_id", "companies", ["owner_id"])
    op.create_index("ix_companies_owner_name", "companies", ["owner_id", "name"])

    # subscription_packages
    op.create_table(
        "subscription_packages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("max_companies", sa.Integer, nullable=False, server_default="5"),
        sa.Column("max_reports_per_month", sa.Integer, nullable=False, server_default="10"),
        sa.Column("max_ai_calls_per_month", sa.Integer, nullable=False, server_default="50"),
        sa.Column("features", sa.JSON),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # user_subscriptions
    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("package_id", sa.Integer, sa.ForeignKey("subscription_packages.id"), nullable=False),
        sa.Column("status", sa.Enum("active", "expired", "cancelled", "pending", name="subscriptionstatus"), nullable=False, server_default="pending"),
        sa.Column("start_date", sa.DateTime),
        sa.Column("end_date", sa.DateTime),
        sa.Column("ai_calls_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reports_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_subscriptions_user_status", "user_subscriptions", ["user_id", "status"])
    op.create_index("ix_subscriptions_end_date", "user_subscriptions", ["end_date"])

    # purchase_requests
    op.create_table(
        "purchase_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("package_id", sa.Integer, sa.ForeignKey("subscription_packages.id"), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "cancelled", name="purchasestatus"), nullable=False, server_default="pending"),
        sa.Column("admin_note", sa.Text),
        sa.Column("reviewed_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime),
    )
    op.create_index("ix_purchase_status_created", "purchase_requests", ["status", "created_at"])
    op.create_index("ix_purchase_user_status", "purchase_requests", ["user_id", "status"])

    # financial_reports
    op.create_table(
        "financial_reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type", sa.Enum("balance_sheet", "income_statement", "cash_flow", "combined", name="reporttype"), nullable=False),
        sa.Column("period", sa.Enum("annual", "q1", "q2", "q3", "q4", name="periodtype"), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("source_document", sa.String(500)),
        sa.Column("is_ai_generated", sa.Boolean, server_default="false"),
        sa.Column("is_verified", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime),
        # Balance sheet - encrypted (stored as Text)
        sa.Column("cash_and_equivalents", sa.Text), sa.Column("short_term_investments", sa.Text),
        sa.Column("accounts_receivable", sa.Text), sa.Column("inventory", sa.Text),
        sa.Column("other_current_assets", sa.Text), sa.Column("total_current_assets", sa.Text),
        sa.Column("property_plant_equipment", sa.Text), sa.Column("intangible_assets", sa.Text),
        sa.Column("long_term_investments", sa.Text), sa.Column("total_non_current_assets", sa.Text),
        sa.Column("total_assets", sa.Text), sa.Column("accounts_payable", sa.Text),
        sa.Column("short_term_debt", sa.Text), sa.Column("current_portion_long_term_debt", sa.Text),
        sa.Column("other_current_liabilities", sa.Text), sa.Column("total_current_liabilities", sa.Text),
        sa.Column("long_term_debt", sa.Text), sa.Column("deferred_tax_liabilities", sa.Text),
        sa.Column("total_non_current_liabilities", sa.Text), sa.Column("total_liabilities", sa.Text),
        sa.Column("share_capital", sa.Text), sa.Column("retained_earnings", sa.Text),
        sa.Column("other_equity", sa.Text), sa.Column("total_equity", sa.Text),
        # Income statement
        sa.Column("revenue", sa.Text), sa.Column("cost_of_goods_sold", sa.Text),
        sa.Column("gross_profit", sa.Text), sa.Column("operating_expenses", sa.Text),
        sa.Column("ebitda", sa.Text), sa.Column("ebit", sa.Text),
        sa.Column("interest_expense", sa.Text), sa.Column("income_before_tax", sa.Text),
        sa.Column("income_tax", sa.Text), sa.Column("net_income", sa.Text),
        # Cash flow
        sa.Column("operating_cash_flow", sa.Text), sa.Column("investing_cash_flow", sa.Text),
        sa.Column("financing_cash_flow", sa.Text), sa.Column("free_cash_flow", sa.Text),
        sa.Column("net_change_in_cash", sa.Text),
        # AI
        sa.Column("ai_analysis", sa.JSON), sa.Column("ai_ratios", sa.JSON),
    )
    op.create_index("ix_financial_company_year", "financial_reports", ["company_id", "fiscal_year"])
    op.create_index("ix_financial_company_period", "financial_reports", ["company_id", "period"])
    op.create_index("ix_financial_type_year", "financial_reports", ["report_type", "fiscal_year"])
    op.create_index("ix_financial_company_type_year", "financial_reports", ["company_id", "report_type", "fiscal_year"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.Enum("create", "read", "update", "delete", "login", "logout", "export", "upload", name="logaction"), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer),
        sa.Column("old_values", sa.JSON), sa.Column("new_values", sa.JSON),
        sa.Column("ip_address", sa.String(45)), sa.Column("user_agent", sa.String(500)),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_user_timestamp", "audit_logs", ["user_id", "timestamp"])
    op.create_index("ix_audit_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_action_timestamp", "audit_logs", ["action", "timestamp"])

    # ai_operation_logs
    op.create_table(
        "ai_operation_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("service", sa.String(50), nullable=False),
        sa.Column("model_used", sa.String(100)),
        sa.Column("prompt_tokens", sa.Integer), sa.Column("completion_tokens", sa.Integer),
        sa.Column("total_tokens", sa.Integer), sa.Column("duration_ms", sa.Float),
        sa.Column("success", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("error_type", sa.String(100)), sa.Column("error_message", sa.Text),
        sa.Column("request_metadata", sa.JSON), sa.Column("response_metadata", sa.JSON),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_log_service_date", "ai_operation_logs", ["service", "created_at"])
    op.create_index("ix_ai_log_success_date", "ai_operation_logs", ["success", "created_at"])
    op.create_index("ix_ai_log_user_date", "ai_operation_logs", ["user_id", "created_at"])

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("purchase_request", "purchase_approved", "purchase_rejected", "report_ready", "system", name="notificationtype"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("meta", sa.JSON),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read"])
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("ai_operation_logs")
    op.drop_table("audit_logs")
    op.drop_table("financial_reports")
    op.drop_table("purchase_requests")
    op.drop_table("user_subscriptions")
    op.drop_table("subscription_packages")
    op.drop_table("companies")
    op.drop_table("users")
