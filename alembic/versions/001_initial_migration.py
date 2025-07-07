"""Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'SELLER', 'BUYER', name='userrole'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING', name='userstatus'), nullable=False),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(length=45), nullable=True),
        sa.Column('login_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)

    # Create categories table
    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('meta_title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('meta_keywords', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('product_count', sa.Integer(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=False)
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=False)
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)
    op.create_index(op.f('ix_categories_is_active'), 'categories', ['is_active'], unique=False)
    op.create_index(op.f('ix_categories_is_featured'), 'categories', ['is_featured'], unique=False)
    op.create_index(op.f('ix_categories_display_order'), 'categories', ['display_order'], unique=False)

    # Create brands table
    op.create_table('brands',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('company_name', sa.String(length=200), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('meta_title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('meta_keywords', sa.String(length=500), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('product_count', sa.Integer(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('review_count', sa.Integer(), nullable=False),
        sa.Column('social_media', sa.JSON(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_brands_name'), 'brands', ['name'], unique=False)
    op.create_index(op.f('ix_brands_slug'), 'brands', ['slug'], unique=False)
    op.create_index(op.f('ix_brands_is_active'), 'brands', ['is_active'], unique=False)
    op.create_index(op.f('ix_brands_is_featured'), 'brands', ['is_featured'], unique=False)
    op.create_index(op.f('ix_brands_is_verified'), 'brands', ['is_verified'], unique=False)
    op.create_index(op.f('ix_brands_display_order'), 'brands', ['display_order'], unique=False)
    op.create_index(op.f('ix_brands_rating'), 'brands', ['rating'], unique=False)

    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=220), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('compare_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=False),
        sa.Column('low_stock_threshold', sa.Integer(), nullable=False),
        sa.Column('track_inventory', sa.Boolean(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('dimension_unit', sa.String(length=10), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED', name='productstatus'), nullable=False),
        sa.Column('visibility', sa.Enum('PUBLIC', 'PRIVATE', 'HIDDEN', name='productvisibility'), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('is_digital', sa.Boolean(), nullable=False),
        sa.Column('requires_shipping', sa.Boolean(), nullable=False),
        sa.Column('meta_title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('meta_keywords', sa.String(length=500), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('sales_count', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('review_count', sa.Integer(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_slug'), 'products', ['slug'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_index(op.f('ix_products_brand_id'), 'products', ['brand_id'], unique=False)
    op.create_index(op.f('ix_products_price'), 'products', ['price'], unique=False)
    op.create_index(op.f('ix_products_status'), 'products', ['status'], unique=False)
    op.create_index(op.f('ix_products_visibility'), 'products', ['visibility'], unique=False)
    op.create_index(op.f('ix_products_is_featured'), 'products', ['is_featured'], unique=False)
    op.create_index(op.f('ix_products_rating'), 'products', ['rating'], unique=False)
    op.create_index(op.f('ix_products_created_at'), 'products', ['created_at'], unique=False)

    # Create product_images table
    op.create_table('product_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('alt_text', sa.String(length=200), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_images_product_id'), 'product_images', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_images_display_order'), 'product_images', ['display_order'], unique=False)
    op.create_index(op.f('ix_product_images_is_primary'), 'product_images', ['is_primary'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order
    op.drop_table('product_images')
    op.drop_table('products')
    op.drop_table('brands')
    op.drop_table('categories')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS productstatus')
    op.execute('DROP TYPE IF EXISTS productvisibility')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS userstatus')