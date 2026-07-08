import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Constraint,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    role = relationship("Role", back_populates="users")
    uploads = relationship("UploadHistory", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    workspaces = relationship("Workspace", back_populates="owner", cascade="all, delete-orphan")

class Workspace(Base):
    __tablename__ = "workspaces"
    
    workspace_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    owner = relationship("User", back_populates="workspaces")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.workspace_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    workspace = relationship("Workspace", back_populates="projects")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")

class Store(Base):
    __tablename__ = "stores"
    
    store_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_code = Column(String(20), unique=True, nullable=False, index=True)
    store_name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    orders = relationship("Order", back_populates="store")
    employees = relationship("Employee", back_populates="store")
    inventories = relationship("Inventory", back_populates="store")

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = Column(String(100), unique=True, nullable=False)
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="SET NULL"), nullable=True)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(150), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    insightflow_price = Column(Numeric(12, 2), nullable=False)
    
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="chk_cost_price_positive"),
        CheckConstraint("insightflow_price >= 0", name="chk_insightflow_price_positive"),
        CheckConstraint("insightflow_price >= cost_price", name="chk_price_relationship"),
    )
    
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    inventories = relationship("Inventory", back_populates="product")

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_code = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True)
    segment = Column(String(30), default="Unassigned")
    registration_date = Column(Date, nullable=False)
    
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id", ondelete="SET NULL"), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="RESTRICT"), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_total_amount_positive"),
    )
    
    customer = relationship("Customer", back_populates="orders")
    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    order_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    net_amount = Column(Numeric(12, 2), nullable=False)
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_unit_price_positive"),
        CheckConstraint("net_amount >= 0", name="chk_net_amount_positive"),
    )
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    returns = relationship("Return", back_populates="order_item")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    supplier_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_name = Column(String(100), nullable=False)
    contact_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    
    inventories = relationship("Inventory", back_populates="supplier")

class Inventory(Base):
    __tablename__ = "inventory"
    
    inventory_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="RESTRICT"), nullable=False)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    safety_stock = Column(Integer, nullable=False, default=10)
    reorder_point = Column(Integer, nullable=False, default=20)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.supplier_id", ondelete="SET NULL"), nullable=True)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="chk_qty_on_hand_positive"),
        CheckConstraint("safety_stock >= 0", name="chk_safety_stock_positive"),
        CheckConstraint("reorder_point >= 0", name="chk_reorder_point_positive"),
    )
    
    product = relationship("Product", back_populates="inventories")
    store = relationship("Store", back_populates="inventories")
    supplier = relationship("Supplier", back_populates="inventories")

class Employee(Base):
    __tablename__ = "employees"
    
    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="RESTRICT"), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    salary = Column(Numeric(12, 2), nullable=False)
    hire_date = Column(Date, nullable=False)
    
    store = relationship("Store", back_populates="employees")

class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False, default="Success")
    
    order = relationship("Order", back_populates="payments")

class Return(Base):
    __tablename__ = "returns"
    
    return_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.order_item_id", ondelete="CASCADE"), nullable=False)
    return_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    refund_amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), nullable=True)
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_return_qty_positive"),
        CheckConstraint("refund_amount >= 0", name="chk_refund_amount_positive"),
    )
    
    order_item = relationship("OrderItem", back_populates="returns")

class UploadHistory(Base):
    __tablename__ = "upload_history"
    
    upload_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), nullable=False, default="Pending")
    records_processed = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="uploads")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(50), nullable=True)
    record_id = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="audit_logs")

class Dataset(Base):
    __tablename__ = "datasets"
    
    dataset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False, default="Generic Business Dataset")
    confidence_score = Column(Numeric(5, 2), nullable=False, default=100.0)
    record_count = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    project = relationship("Project", back_populates="datasets")
    columns = relationship("ColumnMetadata", back_populates="dataset", cascade="all, delete-orphan")
    kpis = relationship("GeneratedKPI", back_populates="dataset", cascade="all, delete-orphan")
    insights = relationship("GeneratedInsight", back_populates="dataset", cascade="all, delete-orphan")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    
    version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False, default="Original")  # Original, Cleaned, Transformed, Feature_Engineered, Forecast_Ready
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    description = Column(Text, nullable=True)
    
    dataset = relationship("Dataset", back_populates="versions")

class ColumnMetadata(Base):
    __tablename__ = "column_metadata"
    
    column_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(150), nullable=False)
    data_type = Column(String(50), nullable=False)
    semantic_type = Column(String(50), nullable=False, default="Text")
    null_percentage = Column(Numeric(5, 2), default=0.0)
    distinct_count = Column(Integer, default=0)
    min_value = Column(String(100), nullable=True)
    max_value = Column(String(100), nullable=True)
    mean_value = Column(Numeric(18, 4), nullable=True)
    median_value = Column(Numeric(18, 4), nullable=True)
    std_dev_value = Column(Numeric(18, 4), nullable=True)
    
    dataset = relationship("Dataset", back_populates="columns")

class DatasetRelationship(Base):
    __tablename__ = "dataset_relationships"
    
    relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    target_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    source_column = Column(String(150), nullable=False)
    target_column = Column(String(150), nullable=False)
    relationship_type = Column(String(50), nullable=False, default="One-to-Many")
    confidence = Column(Numeric(5, 2), default=100.0)

class GeneratedKPI(Base):
    __tablename__ = "generated_kpis"
    
    kpi_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    kpi_name = Column(String(100), nullable=False)
    formula = Column(Text, nullable=False)
    display_value = Column(String(100), nullable=True)
    
    dataset = relationship("Dataset", back_populates="kpis")

class GeneratedInsight(Base):
    __tablename__ = "generated_insights"
    
    insight_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    severity = Column(String(30), default="info")
    
    dataset = relationship("Dataset", back_populates="insights")
