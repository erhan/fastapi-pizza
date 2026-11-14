"""pizzas, users and orders

Revision ID: 0001
Revises:
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "pizzas",
        sa.Column("id", sa.Integer(), primary_key=True),
        created_at(),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("size", sa.String(10), nullable=False),
        sa.Column("toppings", sa.JSON(), nullable=False),
        sa.Column("is_vegetarian", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_pizzas_is_vegetarian", "pizzas", ["is_vegetarian"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        created_at(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(60), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        created_at(),
        sa.Column("pizza_id", sa.Integer(), sa.ForeignKey("pizzas.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("pizza_name", sa.String(40), nullable=False),
        sa.Column("customer_name", sa.String(60), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
    )
    op.create_index("ix_orders_pizza_id", "orders", ["pizza_id"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])


def downgrade() -> None:
    op.drop_table("orders")
    op.drop_table("users")
    op.drop_table("pizzas")
